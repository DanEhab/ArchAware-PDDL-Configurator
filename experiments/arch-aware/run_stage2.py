"""
Run Stage 2 -- Architecture-Aware Execution Pipeline
====================================================
Main orchestrator for Stage 2.

Usage:
    python -m experiments.arch-aware.run_stage2

Coordinates:
  - Validation Pipeline Output
  - Planner Execution (up to 1,200 runs via ThreadPool)
  - Each domain runs on its target planner ONLY.

Features:
  - Validated domain logic: only runs planners on domains that passed validation
  - Dual CSV writes (global + local)
  - 60-second heartbeat & graceful exit
  - Terminal output mirrored to log file
"""

import sys
import signal
import time
import atexit
import csv
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Add the arch-aware directory to sys.path so we can import internal modules easily
sys.path.insert(0, str(PROJECT_ROOT / "experiments" / "arch-aware"))

CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

from csv_manager_stage2 import CSVManagerStage2
from planner_runner_stage2 import execute_planner

# -- Reused Base Modules --
from experiments.base.error_handler import ErrorHandler
from experiments.base.heartbeat import HeartbeatThread
from experiments.base.summary_generator import SummaryGenerator

# -- Paths --
GLOBAL_CSV = PROJECT_ROOT / "results" / "planner_execution_data.csv"
LOCAL_CSV = PROJECT_ROOT / "results" / "arch_aware" / "arch_aware_planner_execution_data.csv"
LLM_CSV_PATH = PROJECT_ROOT / "results" / "arch_aware" / "LLM Results" / "arch_aware_llm_generation_data.csv"
VALIDATED_DOMAINS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Validated Domains"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# Logs
LOG_DIR = PROJECT_ROOT / "logs" / "stage2"
HEARTBEAT_PATH = LOG_DIR / "pipeline_heartbeat.log"
SUMMARIES_DIR = LOG_DIR / "run_summaries"
ERROR_REGISTER = LOG_DIR / "error_register.csv"
ERROR_DUMPS = LOG_DIR / "error_dumps"
TERMINAL_LOG_DIR = LOG_DIR / "terminal_output"

# -- Config --
DOCKER_CFG = {
    "cpus": CONFIG["docker"]["cpus"],
    "memory": CONFIG["docker"]["memory"],
    "memory_swap": CONFIG["docker"]["memory_swap"],
    "timeout_seconds": CONFIG["docker"]["timeout_seconds"],
}

PLANNERS = [
    {"name": p["name"], "docker_image": p["docker_image"]}
    for p in CONFIG["planners"]
]

PROMPT_ID_TO_PLANNER = {
    "1": "lama",
    "2": "decstar",
    "3": "bfws",
    "4": "madagascar"
}

# ====================================================================== #
# TeeLogger                                                              #
# ====================================================================== #
class TeeLogger:
    def __init__(self, log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._terminal = sys.stdout
        self._log_file = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self._terminal.write(message)
        self._log_file.write(message)
        self._log_file.flush()

    def flush(self):
        self._terminal.flush()
        self._log_file.flush()

    def close(self):
        self._log_file.close()

# ====================================================================== #
# Sub-Pipelines                                                          #
# ====================================================================== #
def run_child_script(script_path: Path):
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, process.args)

def check_llm_pipeline():
    print("[INFO] Checking LLM Generation Phase (Stage 2)...")
    if LLM_CSV_PATH.exists():
        with open(LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
            lines = list(csv.DictReader(f))
            if len(lines) >= 80:
                print(f"  -> Found {len(lines)} generated domains. Skipping LLM execution.\n")
                return

    print("  -> Running LLM Generation Pipeline...")
    script_path = PROJECT_ROOT / "experiments" / "arch-aware" / "llms" / "stage2_arch_aware_pipeline.py"
    run_child_script(script_path)
    print("  -> LLM Generation Phase Complete.\n")

def check_validation_pipeline():
    print("[INFO] Checking Validation Phase (Stage 2)...")
    needs_validation = False
    
    if not LLM_CSV_PATH.exists():
        needs_validation = True
    else:
        with open(LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if not row.get("Validation Status") or row["Validation Status"] == "N/A":
                    needs_validation = True
                    break

    if not needs_validation:
        print("  -> All existing LLM domains are validated. Skipping Validation execution.\n")
        return

    print("  -> Running Validation Pipeline...")
    script_path = PROJECT_ROOT / "experiments" / "arch-aware" / "validation" / "run_stage2_validation.py"
    run_child_script(script_path)
    print("  -> Validation Phase Complete.\n")

# ====================================================================== #
# Planner Work Queue                                                     #
# ====================================================================== #
def build_work_queue() -> list:
    queue = []
    valid_domains = []

    model_to_short = {llm["model_id"]: llm["name"] for llm in CONFIG["llms"]}

    if not LLM_CSV_PATH.exists():
        return queue
        
    with open(LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("Validation Status") == "VALID":
                valid_domains.append({
                    "domain_name": row["Domain Name"],
                    "llm_name": row["LLM Model"],
                    "prompt_id": row["Prompt ID"]
                })

    print(f"[INFO] Found {len(valid_domains)} VALID LLM-generated domains.")

    for v in valid_domains:
        d_name = v["domain_name"]
        llm_model_id = v["llm_name"]
        pid = str(v["prompt_id"]).strip()
        
        target_planner = PROMPT_ID_TO_PLANNER.get(pid)
        if not target_planner:
            print(f"[WARNING] Unrecognized Prompt ID {pid}. Skipping.")
            continue

        llm_short = model_to_short.get(llm_model_id)
        if not llm_short:
            print(f"[WARNING] Unrecognized LLM Model ID in CSV: {llm_model_id}")
            continue

        d_path = VALIDATED_DOMAINS_DIR / d_name / target_planner / f"{d_name}_{llm_short}_Arch_Aware_{target_planner}.pddl"
        if not d_path.exists():
            print(f"[WARNING] Validated file missing: {d_path.relative_to(PROJECT_ROOT)}")
            continue

        p_dir = BENCHMARKS_DIR / d_name / "instances"
        if not p_dir.exists():
            continue

        for inst in sorted(p_dir.glob("instance-*.pddl")):
            queue.append((d_name, llm_model_id, d_path, inst, target_planner, pid))

    return queue

# ====================================================================== #
# Thread Worker                                                          #
# ====================================================================== #
def run_planner_workload(
    planner_info: dict,
    work_queue: list,
    csv_mgr: CSVManagerStage2,
    err_handler: ErrorHandler,
    heartbeat: HeartbeatThread,
) -> dict:
    planner_name = planner_info["name"]
    docker_image = planner_info["docker_image"]
    counts = {"SUCCESS": 0, "TIMEOUT": 0, "MEMOUT": 0, "FAILURE": 0}

    assigned_tasks = [item for item in work_queue if item[4] == planner_name]

    if not assigned_tasks:
        print(f"[INFO] No valid Arch-Aware domains targeted for {planner_name}.")
        return counts

    print(f"  [{planner_name}] Processing {len(assigned_tasks)} instance files...")

    for d_name, llm, d_path, p_path, target_planner, pid in assigned_tasks:
        p_name = p_path.name

        if csv_mgr.is_completed(d_name, p_name, planner_name, llm):
            print(f"  [SKIP] {planner_name} | {d_name}/{llm}/{p_name} (checkpointed)")
            continue

        print(f"  [RUN]  {planner_name} | {d_name}/{llm}/{p_name} ...")

        result = execute_planner(
            planner_name=planner_name,
            docker_image=docker_image,
            domain_path=d_path,
            problem_path=p_path,
            docker_cfg=DOCKER_CFG,
        )

        status = result.get("Output_Status", "FAILURE")

        if status == "DOCKER_DAEMON_ERROR":
            err_handler.log_system_error(
                error_type="DOCKER_DAEMON",
                error_message=result.get("_stderr", "Docker daemon error"),
                domain=d_name,
                problem=p_name,
                planner=planner_name,
            )
            print("\n[FATAL] Docker daemon is unreachable. HALTING.\n")
            raise SystemExit(1)

        row = {
            "Domain_Name": d_name,
            "Domain_File": d_path.name,
            "Problem_Instance": p_name,
            "Planner_Used": planner_name,
            "Stage": "Arch_Aware",
            "LLM_Used": llm,
            "PromptID": pid,
            "PlanCost": result.get("PlanCost"),
            "Runtime_internal_s": result.get("Runtime_internal_s"),
            "Runtime_wall_s": result.get("Runtime_wall_s"),
            "Output_Status": status,
            "StatesExpanded": result.get("StatesExpanded"),
            "StatesGenerated": result.get("StatesGenerated"),
            "StatesEvaluated": result.get("StatesEvaluated"),
            "PeakMemoryKB": result.get("PeakMemoryKB"),
            "Timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            run_id = csv_mgr.append_row(row)
        except (IOError, OSError) as exc:
            err_handler.log_system_error(
                error_type="DISK_FULL",
                error_message=str(exc),
                domain=d_name,
                problem=p_name,
                planner=planner_name,
            )
            print(f"\n[FATAL] Disk write error: {exc}. HALTING.\n")
            raise SystemExit(1)

        if status in ("TIMEOUT", "MEMOUT", "FAILURE"):
            err_handler.log_planner_error(
                run_id=run_id,
                domain=d_name,
                problem=p_name,
                planner=planner_name,
                error_type=status,
                stdout=result.get("_stdout", ""),
                stderr=result.get("_stderr", ""),
            )

        heartbeat.last_completed = f"{d_name}/{llm}/{p_name}/{planner_name}"

        if status in counts:
            counts[status] += 1
        else:
            counts["FAILURE"] += 1

        wall = result.get("Runtime_wall_s")
        wall_str = f"{wall:.1f}s" if wall is not None else "N/A"
        print(f"  [{status:>7}] {planner_name} | {d_name}/{llm}/{p_name} | wall={wall_str}")

    return counts

# ====================================================================== #
# Main Loop                                                              #
# ====================================================================== #
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    TERMINAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    terminal_log_path = TERMINAL_LOG_DIR / f"run_{ts_str}.log"
    sys.stdout = TeeLogger(terminal_log_path)

    print("=" * 70)
    print("  Stage 2 (ARCH-AWARE) Execution Pipeline")
    print("  Architecture-Aware PDDL Configurator")
    print("=" * 70)
    print()

    check_llm_pipeline()
    check_validation_pipeline()

    work_queue = build_work_queue()
    total_runs = len(work_queue)
    print(f"[INFO] Work queue: {len(work_queue)} domain x instance pairs")
    print(f"[INFO] Planners: {[p['name'] for p in PLANNERS]}")
    print(f"[INFO] Total expected runs: {total_runs}\n")

    if total_runs == 0:
        print("[WARNING] Zero runs scheduled. Exiting.")
        return

    csv_mgr = CSVManagerStage2(GLOBAL_CSV, LOCAL_CSV)
    print(f"[CHECKPOINT] Found {csv_mgr.completed_count} previously completed runs across all stages.")
    print(f"[INFO] Global CSV: {GLOBAL_CSV.relative_to(PROJECT_ROOT)}")
    print(f"[INFO] Local CSV:  {LOCAL_CSV.relative_to(PROJECT_ROOT)}\n")

    err_handler = ErrorHandler(ERROR_REGISTER, ERROR_DUMPS)
    summary_gen = SummaryGenerator(
        SUMMARIES_DIR, 
        LOCAL_CSV, 
        total_runs, 
        stage_name="Stage 2 (ARCH-AWARE)"
    )
    
    heartbeat = HeartbeatThread(HEARTBEAT_PATH, total_runs, csv_mgr, 60)
    heartbeat.start()
    
    pipeline_start = time.time()
    summary_generated = False

    def _generate_summary(cause: str):
        nonlocal summary_generated
        if summary_generated: return
        summary_generated = True
        elapsed = time.time() - pipeline_start
        try:
            path = summary_gen.generate(cause=cause, elapsed_seconds=elapsed, error_count=0)
            print(f"\n[SUMMARY] Saved to: {path}")
        except Exception as e:
            print(f"\n[WARNING] Could not write summary: {e}")

    def _signal_handler(signum, frame):
        print("\n\n[INTERRUPT] Received -- shutting down gracefully...")
        heartbeat.stop()
        _generate_summary("SIGINT")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    atexit.register(lambda: _generate_summary("CLEAN_EXIT"))

    print("-" * 70)
    print("  Starting parallel execution (4 planner threads)")
    print("-" * 70)
    print()

    max_workers = CONFIG.get("parallel", {}).get("max_workers", 4)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for p in PLANNERS:
            f = pool.submit(
                run_planner_workload, p, work_queue, csv_mgr, err_handler, heartbeat
            )
            futures[f] = p["name"]

        for f in as_completed(futures):
            pname = futures[f]
            try:
                counts = f.result()
                print(f"\n[DONE] {pname}: SUCCESS={counts.get('SUCCESS',0)} TIMEOUT={counts.get('TIMEOUT',0)} FAILURE={counts.get('FAILURE',0)}")
            except SystemExit:
                pass
            except Exception as exc:
                print(f"\n[ERROR] {pname} crashed: {exc}")

    heartbeat.stop()
    elapsed = time.time() - pipeline_start
    print(f"\n======================================================================")
    print(f"  Stage 2 complete -- time: {int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"======================================================================")

if __name__ == "__main__":
    main()
