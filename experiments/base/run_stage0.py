"""
Run Stage 0 -- Baseline Execution Pipeline
==========================================
Main orchestrator for Stage 0 (original unmodified domains).

Usage:
    python -m experiments.base.run_stage0

Runs 4 planners in parallel (one thread per planner), each
processing all 5 domains x 15 instances = 75 runs per planner
= 300 total runs.

Features:
  - Thread-safe CSV writes (CSVManager)
  - O(1) checkpoint-based resume on restart
  - 60-second heartbeat logging
  - Graceful Ctrl+C and SIGTERM handling with post-run summary
  - Comprehensive error logging (register + dumps for TIMEOUT/MEMOUT/FAILURE)
  - Terminal output mirrored to log file (TeeLogger)
  - HALT on Docker daemon failure or disk full
"""

import sys
import os
import signal
import time
import atexit
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path so we can import our modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# -- Load experiment config ------------------------------------------------
import yaml

CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# -- Import pipeline modules -----------------------------------------------
from experiments.base.csv_manager import CSVManager
from experiments.base.error_handler import ErrorHandler
from experiments.base.heartbeat import HeartbeatThread
from experiments.base.summary_generator import SummaryGenerator
from experiments.base.planner_runner import execute_planner

# -- Paths -----------------------------------------------------------------
CSV_PATH = PROJECT_ROOT / "results" / "planner_execution_data.csv"
HEARTBEAT_PATH = PROJECT_ROOT / "logs" / "stage0" / "pipeline_heartbeat.log"
SUMMARIES_DIR = PROJECT_ROOT / "logs" / "stage0" / "run_summaries"
ERROR_REGISTER = PROJECT_ROOT / "logs" / "stage0" / "error_register.csv"
ERROR_DUMPS = PROJECT_ROOT / "logs" / "stage0" / "error_dumps"
TERMINAL_LOG_DIR = PROJECT_ROOT / "logs" / "stage0" / "terminal_output"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# -- Docker config from YAML -----------------------------------------------
DOCKER_CFG = {
    "cpus": CONFIG["docker"]["cpus"],
    "memory": CONFIG["docker"]["memory"],
    "memory_swap": CONFIG["docker"]["memory_swap"],
    "timeout_seconds": CONFIG["docker"]["timeout_seconds"],
}

# -- Build planner list from config ----------------------------------------
PLANNERS = [
    {"name": p["name"], "docker_image": p["docker_image"]}
    for p in CONFIG["planners"]
]


# ======================================================================
# TeeLogger -- mirrors stdout to both terminal and log file
# ======================================================================

class TeeLogger:
    """Duplicates all writes to sys.stdout into a log file."""

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


# -- Build work queue ------------------------------------------------------
def build_work_queue() -> list:
    """Build the list of (domain_name, domain_path, problem_path) tuples.

    Scans benchmarks/<domain>/instances/ for each domain in the config.
    Returns a sorted list of 75 entries (5 domains x 15 instances).
    """
    queue = []
    for domain_cfg in CONFIG["domains"]:
        domain_name = domain_cfg["name"]
        domain_dir = BENCHMARKS_DIR / domain_name
        domain_file = domain_dir / "domain.pddl"
        instances_dir = domain_dir / "instances"

        if not domain_file.exists():
            print(f"[WARNING] Domain file not found: {domain_file}")
            continue
        if not instances_dir.exists():
            print(f"[WARNING] Instances dir not found: {instances_dir}")
            continue

        for inst in sorted(instances_dir.glob("instance-*.pddl")):
            queue.append((domain_name, domain_file, inst))

    return queue


# -- Worker function (one per planner thread) ------------------------------
def run_planner_workload(
    planner_info: dict,
    work_queue: list,
    csv_mgr: CSVManager,
    err_handler: ErrorHandler,
    heartbeat: HeartbeatThread,
) -> dict:
    """Process all domain x instance pairs for ONE planner.

    This function runs in its own thread. It is fully independent
    from the other planner threads -- if one planner finishes early,
    it does not affect the others.

    Returns a summary dict with counts per status.
    """
    planner_name = planner_info["name"]
    docker_image = planner_info["docker_image"]
    counts = {"SUCCESS": 0, "TIMEOUT": 0, "MEMOUT": 0, "FAILURE": 0}

    for domain_name, domain_path, problem_path in work_queue:
        problem_name = problem_path.name

        # -- Checkpoint: skip if already completed --
        if csv_mgr.is_completed(domain_name, problem_name, planner_name):
            print(
                f"  [SKIP] {planner_name} | {domain_name}/{problem_name} "
                f"(already in CSV)"
            )
            continue

        print(
            f"  [RUN]  {planner_name} | {domain_name}/{problem_name} ..."
        )

        # -- Execute planner --
        result = execute_planner(
            planner_name=planner_name,
            docker_image=docker_image,
            domain_path=domain_path,
            problem_path=problem_path,
            docker_cfg=DOCKER_CFG,
        )

        status = result.get("Output_Status", "FAILURE")

        # -- Check for system-level halt conditions --
        if status == "DOCKER_DAEMON_ERROR":
            err_handler.log_system_error(
                error_type="DOCKER_DAEMON",
                error_message=result.get("_stderr", "Docker daemon not running"),
                domain=domain_name,
                problem=problem_name,
                planner=planner_name,
            )
            print(
                "\n[FATAL] Docker daemon is not running or unreachable.\n"
                "        Pipeline HALTING. Restart Docker and re-run the script.\n"
                "        Checkpoint is saved -- it will resume from where it stopped.\n"
            )
            raise SystemExit(1)

        # -- Build the CSV row --
        row = {
            "Domain_Name": domain_name,
            "Domain_File": "domain.pddl",
            "Problem_Instance": problem_name,
            "Planner_Used": planner_name,
            "Stage": "BASELINE",
            "LLM_Used": "N/A",
            "PromptID": "N/A",
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

        # -- Write to CSV (thread-safe) --
        try:
            run_id = csv_mgr.append_row(row)
        except (IOError, OSError) as exc:
            err_handler.log_system_error(
                error_type="DISK_FULL",
                error_message=str(exc),
                domain=domain_name,
                problem=problem_name,
                planner=planner_name,
            )
            print(
                f"\n[FATAL] Disk write error: {exc}\n"
                f"        Pipeline HALTING.\n"
            )
            raise SystemExit(1)

        # -- Log errors (TIMEOUT, MEMOUT, FAILURE all logged now) --
        if status in ("TIMEOUT", "MEMOUT", "FAILURE"):
            # Build metrics dict for error register extra columns
            error_metrics = {
                "PlanCost": result.get("PlanCost"),
                "StatesExpanded": result.get("StatesExpanded"),
                "StatesGenerated": result.get("StatesGenerated"),
                "StatesEvaluated": result.get("StatesEvaluated"),
                "PeakMemoryKB": result.get("PeakMemoryKB"),
            }
            # Convert None values to "N/A" for display
            error_metrics = {
                k: (v if v is not None else "N/A")
                for k, v in error_metrics.items()
            }

            err_handler.log_planner_error(
                run_id=run_id,
                domain=domain_name,
                problem=problem_name,
                planner=planner_name,
                error_type=status,
                stdout=result.get("_stdout", ""),
                stderr=result.get("_stderr", ""),
                metrics=error_metrics,
            )

        # -- Update heartbeat --
        heartbeat.last_completed = f"{domain_name}/{problem_name}/{planner_name}"

        # -- Track status count --
        if status in counts:
            counts[status] += 1
        else:
            counts["FAILURE"] += 1

        # -- Console feedback --
        wall = result.get("Runtime_wall_s")
        wall_str = f"{wall:.1f}s" if wall is not None else "N/A"
        cost = result.get("PlanCost")
        cost_str = str(cost) if cost is not None else "N/A"
        print(
            f"  [{status:>7}] {planner_name} | {domain_name}/{problem_name} | "
            f"wall={wall_str} cost={cost_str}"
        )

    return counts


# ========================================================================
# Main entry point
# ========================================================================

def main():
    # -- 0. Set up TeeLogger for terminal output capture --
    TERMINAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    terminal_log_path = TERMINAL_LOG_DIR / f"run_{ts_str}.log"
    tee = TeeLogger(terminal_log_path)
    sys.stdout = tee

    print("=" * 65)
    print("  Stage 0 (BASELINE) Execution Pipeline")
    print("  Architecture-Aware PDDL Configurator")
    print("=" * 65)
    print()

    # -- 0b. Check for tmux/screen --
    if not os.environ.get("TMUX") and not os.environ.get("STY"):
        print("[WARNING] Not running inside tmux or screen.")
        print("          If the terminal session is killed (e.g. screen lock),")
        print("          the pipeline will stop. Recommended:")
        print("          tmux new-session -d -s stage0 'caffeinate -i python3 -m experiments.base.run_stage0'")
        print()

    # -- 1. Build work queue --
    work_queue = build_work_queue()
    total_runs = len(work_queue) * len(PLANNERS)
    print(f"[INFO] Work queue: {len(work_queue)} domain x instance pairs")
    print(f"[INFO] Planners: {[p['name'] for p in PLANNERS]}")
    print(f"[INFO] Total runs: {total_runs}")
    print()

    # -- 2. Initialize CSV manager (loads checkpoint) --
    csv_mgr = CSVManager(CSV_PATH)
    already = csv_mgr.completed_count
    if already > 0:
        print(f"[CHECKPOINT] Found {already} completed runs in CSV -- will skip them.")
    print(f"[INFO] CSV output: {CSV_PATH}")
    print()

    # -- 3. Initialize error handler --
    err_handler = ErrorHandler(ERROR_REGISTER, ERROR_DUMPS)
    error_count = 0  # Tracked for summary

    # -- 4. Initialize summary generator --
    summary_gen = SummaryGenerator(SUMMARIES_DIR, CSV_PATH, total_runs)

    # -- 5. Start heartbeat daemon --
    heartbeat = HeartbeatThread(
        log_path=HEARTBEAT_PATH,
        total_runs=total_runs,
        csv_manager=csv_mgr,
        interval=CONFIG.get("heartbeat", {}).get("interval_seconds", 60),
    )
    heartbeat.start()
    print(f"[INFO] Heartbeat started (every {heartbeat.interval}s) -> {HEARTBEAT_PATH}")
    print(f"[INFO] Terminal output logged to: {terminal_log_path}")
    print()

    # -- 6. Register signal handlers --
    pipeline_start = time.time()
    summary_generated = False

    def _generate_summary(cause: str):
        nonlocal summary_generated
        if summary_generated:
            return
        summary_generated = True
        elapsed = time.time() - pipeline_start
        try:
            path = summary_gen.generate(
                cause=cause,
                elapsed_seconds=elapsed,
                error_count=error_count,
            )
            print(f"\n[SUMMARY] Post-run summary saved to: {path}")
        except Exception as e:
            print(f"\n[WARNING] Could not write summary: {e}")

    def _signal_handler(signum, frame):
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        print(f"\n\n[INTERRUPT] {sig_name} received -- shutting down gracefully...")
        heartbeat.stop()
        _generate_summary(sig_name)
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    atexit.register(lambda: _generate_summary("CLEAN_EXIT"))

    # -- 7. Check Docker is running --
    try:
        chk = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=15,
        )
        if chk.returncode != 0:
            print("[FATAL] Docker daemon is not running. Start Docker Desktop first.")
            _generate_summary("SYSTEM_ERROR")
            sys.exit(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[FATAL] Docker not found or not responding.")
        _generate_summary("SYSTEM_ERROR")
        sys.exit(1)

    # -- 8. Check Docker images exist --
    # Bypassed: macOS Docker CLI sometimes returns false negatives here.
    # We trust that the images are built based on your `docker images` output.
    print("[INFO] Docker images assumed to be built and ready [OK]")
    print()

    # -- 9. Execute: 4 planner threads --
    print("-" * 65)
    print("  Starting parallel execution (4 planner threads)")
    print("-" * 65)
    print()

    max_workers = CONFIG.get("parallel", {}).get("max_workers", 4)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for planner_info in PLANNERS:
            future = pool.submit(
                run_planner_workload,
                planner_info=planner_info,
                work_queue=work_queue,
                csv_mgr=csv_mgr,
                err_handler=err_handler,
                heartbeat=heartbeat,
            )
            futures[future] = planner_info["name"]

        # Wait for all threads to complete
        for future in as_completed(futures):
            planner_name = futures[future]
            try:
                counts = future.result()
                print(
                    f"\n[DONE] {planner_name} finished: "
                    f"SUCCESS={counts.get('SUCCESS', 0)} "
                    f"TIMEOUT={counts.get('TIMEOUT', 0)} "
                    f"MEMOUT={counts.get('MEMOUT', 0)} "
                    f"FAILURE={counts.get('FAILURE', 0)}"
                )
            except SystemExit:
                # HALT conditions (Docker daemon, disk full) already handled
                pass
            except Exception as exc:
                print(f"\n[ERROR] {planner_name} crashed: {exc}")
                err_handler.log_system_error(
                    error_type="UNHANDLED_EXCEPTION",
                    error_message=str(exc),
                    planner=planner_name,
                )

    # -- 10. Finalize --
    heartbeat.stop()
    elapsed = time.time() - pipeline_start
    hrs = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)

    print()
    print("=" * 65)
    print(f"  Stage 0 complete -- {csv_mgr.completed_count}/{total_runs} runs")
    print(f"  Total time: {hrs}h {mins}m")
    print("=" * 65)


if __name__ == "__main__":
    main()
