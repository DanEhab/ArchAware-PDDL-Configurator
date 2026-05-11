"""
Run Cross Test Pipeline (Phase E)
====================================================
Main orchestrator for Stage 2 Cross Test.

Usage:
    python -m experiments.arch-aware.cross_test.run_cross_test

Coordinates:
  - Reads improved domains from improvement_results.csv
  - Runs each valid improved domain against the 3 non-target planners
  - Runs on all 15 instances.
"""

import sys
import signal
import time
import atexit
import csv
import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments" / "arch-aware"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments" / "arch-aware" / "cross_test"))

CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

from csv_manager_cross_test import CSVManagerCrossTest
from planner_runner_stage2 import execute_planner

from experiments.base.error_handler import ErrorHandler
from experiments.base.heartbeat import HeartbeatThread
from experiments.base.summary_generator import SummaryGenerator

# -- Paths --
GLOBAL_CSV = PROJECT_ROOT / "results" / "planner_execution_data.csv"
LOCAL_CSV = PROJECT_ROOT / "results" / "cross_test" / "cross_test_planner_execution_data.csv"
IMPROVED_DOMAINS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Improved Domains"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
IMPROVEMENT_CSV = PROJECT_ROOT / "results" / "arch_aware" / "improvement" / "improvement_results.csv"

# Logs
LOG_DIR = PROJECT_ROOT / "logs" / "stage2" / "cross_test"
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
ALL_PLANNER_NAMES = [p["name"] for p in PLANNERS]

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
        self._terminal.flush()
        self._log_file.write(message)
        self._log_file.flush()

    def flush(self):
        self._terminal.flush()

# ====================================================================== #
# Planner Work Queue                                                     #
# ====================================================================== #
def build_work_queue() -> list:
    queue = []
    if not IMPROVEMENT_CSV.exists():
        print(f"[ERROR] Improvement CSV not found at {IMPROVEMENT_CSV}")
        return queue

    df = pd.read_csv(IMPROVEMENT_CSV)
    improved = df[df["IMPROVEMENT_DETECTED"].astype(str).str.lower() == "true"]
    
    model_id_to_name = {llm["model_id"]: llm["name"] for llm in CONFIG["llms"]}

    print(f"[INFO] Found {len(improved)} improved domains to cross-test.")

    for _, row in improved.iterrows():
        domain_name = row["Domain"]
        llm_model_id = row["LLM"]
        target_planner = row["Target_Planner"]
        llm_short = model_id_to_name.get(llm_model_id, llm_model_id)

        domain_file_name = f"{domain_name}_{llm_short}_Arch_Aware_{target_planner}.pddl"
        domain_path = IMPROVED_DOMAINS_DIR / domain_name / target_planner / domain_file_name
        
        if not domain_path.exists():
            print(f"[WARNING] Validated file missing: {domain_path}")
            continue

        p_dir = BENCHMARKS_DIR / domain_name / "instances"
        if not p_dir.exists():
            continue

        instances = sorted(list(p_dir.glob("instance-*.pddl")))
        other_planners = [p for p in ALL_PLANNER_NAMES if p != target_planner]

        for p_name in other_planners:
            for inst in instances:
                queue.append((domain_name, llm_model_id, domain_path, inst, p_name, target_planner))

    return queue

# ====================================================================== #
# Thread Worker                                                          #
# ====================================================================== #
def run_planner_workload(
    planner_info: dict,
    work_queue: list,
    csv_mgr: CSVManagerCrossTest,
    err_handler: ErrorHandler,
    heartbeat: HeartbeatThread
) -> dict:
    planner_name = planner_info["name"]
    docker_image = planner_info["docker_image"]

    counts = {"SUCCESS": 0, "TIMEOUT": 0, "MEMOUT": 0, "FAILURE": 0}

    for item in work_queue:
        # Unpack queue item
        d_name, llm, d_path, p_path, p_name, target_planner_used_in_gen = item
        problem_id = p_path.name

        # We route tasks based on the target execution planner
        if p_name != planner_name:
            continue

        prompt_id_map = {
            "lama": 1,
            "decstar": 2,
            "bfws": 3,
            "madagascar": 4
        }
        prompt_id = prompt_id_map.get(target_planner_used_in_gen, 0)

        if csv_mgr.is_completed(d_name, problem_id, planner_name, llm, prompt_id):
            print(f"  [SKIP] {planner_name} | {d_name}/{llm}/{problem_id} (checkpointed)")
            continue

        print(f"  [RUN]  {planner_name} | {d_name}/{llm}/{problem_id} ...")

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
                problem=problem_id,
                planner=planner_name,
            )
            print("\n[FATAL] Docker daemon is unreachable. HALTING.\n")
            raise SystemExit(1)

        row = {
            "Domain_Name": d_name,
            "Domain_File": d_path.name,
            "Problem_Instance": problem_id,
            "Planner_Used": planner_name,
            "Stage": "Cross_Test",
            "LLM_Used": llm,
            "PromptID": prompt_id,
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
                problem=problem_id,
                planner=planner_name,
            )
            print(f"\n[FATAL] Disk write error: {exc}. HALTING.\n")
            raise SystemExit(1)

        if status in ("TIMEOUT", "MEMOUT", "FAILURE"):
            err_handler.log_planner_error(
                run_id=run_id,
                domain=d_name,
                problem=problem_id,
                planner=planner_name,
                error_type=status,
                stdout=result.get("_stdout", ""),
                stderr=result.get("_stderr", ""),
            )

        heartbeat.last_completed = f"{d_name}/{llm}/{problem_id}/{planner_name}"

        if status in counts:
            counts[status] += 1
        else:
            counts["FAILURE"] += 1

        wall = result.get("Runtime_wall_s")
        wall_str = f"{wall:.1f}s" if wall is not None else "N/A"
        print(f"  [{status:>7}] {planner_name} | {d_name}/{llm}/{problem_id} | wall={wall_str}")

    return counts

# ====================================================================== #
# Main Loop                                                              #
# ====================================================================== #
def main():
    TERMINAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    terminal_log_path = TERMINAL_LOG_DIR / f"run_{ts_str}.log"
    sys.stdout = TeeLogger(terminal_log_path)

    print("=" * 70)
    print("  Stage 2 Cross Test (Phase E) Execution Pipeline")
    print("  Architecture-Aware PDDL Configurator")
    print("=" * 70)
    print()

    work_queue = build_work_queue()
    total_runs = len(work_queue)
    print(f"[INFO] Work queue: {total_runs} domain x planner x instance tuples")
    print(f"[INFO] Planners: {[p['name'] for p in PLANNERS]}")
    print(f"[INFO] Total expected runs: {total_runs}\n")

    if total_runs == 0:
        print("[WARNING] Zero runs scheduled. Exiting.")
        return

    csv_mgr = CSVManagerCrossTest(GLOBAL_CSV, LOCAL_CSV)
    print(f"[CHECKPOINT] Found {csv_mgr.completed_count} previously completed runs across all stages.")
    print(f"[INFO] Global CSV: {GLOBAL_CSV.relative_to(PROJECT_ROOT)}")
    print(f"[INFO] Local CSV:  {LOCAL_CSV.relative_to(PROJECT_ROOT)}\n")

    err_handler = ErrorHandler(ERROR_REGISTER, ERROR_DUMPS)
    summary_gen = SummaryGenerator(
        SUMMARIES_DIR, 
        LOCAL_CSV, 
        total_runs, 
        stage_name="Stage 2 (CROSS-TEST)"
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
    print(f"  Stage 2 Cross Test complete -- time: {int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"======================================================================")

if __name__ == "__main__":
    main()
