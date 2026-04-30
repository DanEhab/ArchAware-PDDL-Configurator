"""
Run Stage 1 -- General Prompt Execution Pipeline
================================================
Main orchestrator for Stage 1 (LLM-modified domains).

Usage:
    python -m experiments.general-prompt.run_stage1

Coordinates:
  1. LLM Generation Pipeline (checks completion)
  2. Validation Pipeline (checks completion)
  3. Planner Execution (1,200 runs via ThreadPool)

Features:
  - Validated domain logic: only runs planners on domains that passed V1-V4
  - Dual CSV writes (global + local)
  - 60-second heartbeat & graceful exit
  - Terminal output mirrored to log file
"""

import sys
import os
import signal
import time
import atexit
import csv
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml

CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# -- Stage 1 specific modules --
# The folder is "general-prompt", which is not a valid Python identifier, 
# so we append it to sys.path to import its contents directly.
sys.path.insert(0, str(PROJECT_ROOT / "experiments" / "general-prompt"))
from csv_manager_stage1 import CSVManagerStage1
from planner_runner_stage1 import execute_planner

# -- Reused Base Modules --
from experiments.base.error_handler import ErrorHandler
from experiments.base.heartbeat import HeartbeatThread
from experiments.base.summary_generator import SummaryGenerator

# -- Paths --
GLOBAL_CSV = PROJECT_ROOT / "results" / "planner_execution_data.csv"
LOCAL_CSV = PROJECT_ROOT / "results" / "general_prompt" / "general_planner_execution_data.csv"
LLM_CSV_PATH = PROJECT_ROOT / "results" / "general_prompt" / "LLM Results" / "general_llm_generation_data.csv"
VALIDATED_DOMAINS_DIR = PROJECT_ROOT / "results" / "general_prompt" / "Validated Domains"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# Logs
LOG_DIR = PROJECT_ROOT / "logs" / "stage1"
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


# ======================================================================
# TeeLogger
# ======================================================================
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

# ======================================================================
# Sub-Pipelines
# ======================================================================
def check_llm_pipeline():
    """Run LLM generation if not already 20 rows."""
    print("[INFO] Checking LLM Generation Phase...")
    if LLM_CSV_PATH.exists():
        with open(LLM_CSV_PATH, "r", encoding="utf-8") as f:
            lines = list(csv.DictReader(f))
            if len(lines) >= 20:
                print(f"  -> Found {len(lines)} generated domains. Skipping LLM execution.\n")
                return

    print("  -> Running LLM Generation Pipeline...")
    script_path = PROJECT_ROOT / "experiments" / "general-prompt" / "llms" / "stage1_general_prompt_pipeline.py"
    subprocess.run(["python", str(script_path)], check=True)
    print("  -> LLM Generation Phase Complete.\n")

def check_validation_pipeline():
    """Run Validation if any rows are missing validation status."""
    print("[INFO] Checking Validation Phase...")
    needs_validation = False
    
    if not LLM_CSV_PATH.exists():
        needs_validation = True
    else:
        with open(LLM_CSV_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("Validation Status") or row["Validation Status"] == "N/A":
                    needs_validation = True
                    break

    if not needs_validation:
        print("  -> All domains are validated. Skipping Validation execution.\n")
        return

    print("  -> Running Validation Pipeline...")
    script_path = PROJECT_ROOT / "experiments" / "general-prompt" / "run_stage1_validation.py"
    subprocess.run(["python", str(script_path)], check=True)
    print("  -> Validation Phase Complete.\n")

# ======================================================================
# Planner Work Queue
# ======================================================================
def build_work_queue() -> list:
    """Build list of (domain_name, llm_name, llm_id, domain_path, problem_path)."""
    queue = []
    valid_domains = []

    # Map model_id to name (used in filenames)
    model_to_short = {llm["model_id"]: llm["name"] for llm in CONFIG["llms"]}

    # Get valid domains
    if not LLM_CSV_PATH.exists():
        return queue
        
    with open(LLM_CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Validation Status") == "VALID":
                valid_domains.append({
                    "domain_name": row["Domain Name"],
                    "llm_name": row["LLM Model"],
                    "prompt_id": row["Prompt ID"]
                })

    print(f"[INFO] Found {len(valid_domains)} VALID LLM-generated domains.")

    # Build matrix
    for v in valid_domains:
        d_name = v["domain_name"]
        llm_model_id = v["llm_name"]
        pid = v["prompt_id"]

        llm_short = model_to_short.get(llm_model_id)
        if not llm_short:
            print(f"[WARNING] Unrecognized LLM Model ID in CSV: {llm_model_id}")
            continue

        # Validate path
        d_path = VALIDATED_DOMAINS_DIR / d_name / f"{d_name}_{llm_short}_General.pddl"
        if not d_path.exists():
            print(f"[WARNING] Validated file missing: {d_path.relative_to(PROJECT_ROOT)}")
            continue

        p_dir = BENCHMARKS_DIR / d_name / "instances"
        if not p_dir.exists():
            continue

        for inst in sorted(p_dir.glob("instance-*.pddl")):
            queue.append((d_name, llm_model_id, pid, d_path, inst))

    return queue

# ======================================================================
# Thread Worker
# ======================================================================
def run_planner_workload(
    planner_info: dict,
    work_queue: list,
    csv_mgr: CSVManagerStage1,
    err_handler: ErrorHandler,
    heartbeat: HeartbeatThread,
) -> dict:
    planner_name = planner_info["name"]
    docker_image = planner_info["docker_image"]
    counts = {"SUCCESS": 0, "TIMEOUT": 0, "MEMOUT": 0, "FAILURE": 0}

    for d_name, llm, pid, d_path, p_path in work_queue:
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
            "Stage": "General",
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

# ======================================================================
# Main Loop
# ======================================================================
def main():
    TERMINAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    terminal_log_path = TERMINAL_LOG_DIR / f"run_{ts_str}.log"
    sys.stdout = TeeLogger(terminal_log_path)

    print("=" * 70)
    print("  Stage 1 (GENERAL PROMPT) Execution Pipeline")
    print("  Architecture-Aware PDDL Configurator")
    print("=" * 70)
    print()

    # Pre-Flight Checks
    check_llm_pipeline()
    check_validation_pipeline()

    # Build Queue
    work_queue = build_work_queue()
    total_runs = len(work_queue) * len(PLANNERS)
    print(f"[INFO] Work queue: {len(work_queue)} domain x instance pairs")
    print(f"[INFO] Planners: {[p['name'] for p in PLANNERS]}")
    print(f"[INFO] Total expected runs: {total_runs}\n")

    if total_runs == 0:
        print("[WARNING] Zero runs scheduled. Exiting.")
        return

    # Checkpoint
    csv_mgr = CSVManagerStage1(GLOBAL_CSV, LOCAL_CSV)
    print(f"[CHECKPOINT] Found {csv_mgr.completed_count} previously completed runs across all stages/LLMs.")
    print(f"[INFO] Global CSV: {GLOBAL_CSV.relative_to(PROJECT_ROOT)}")
    print(f"[INFO] Local CSV:  {LOCAL_CSV.relative_to(PROJECT_ROOT)}\n")

    err_handler = ErrorHandler(ERROR_REGISTER, ERROR_DUMPS)
    summary_gen = SummaryGenerator(SUMMARIES_DIR, GLOBAL_CSV, total_runs)
    
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

    # Execute
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
    print(f"  Stage 1 complete -- time: {int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"======================================================================")

if __name__ == "__main__":
    main()
