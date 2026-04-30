"""
Planner Runner -- Stage 0 Execution Pipeline
=============================================
Executes a single Docker-containerised planner run and returns
a standardised result dict with all metrics.

Handles: SUCCESS, TIMEOUT, MEMOUT, FAILURE, INVALID_OUTPUT
Docker containers use named instances (no --rm) so we can
explicitly kill + remove on timeout.

TIMEOUT STRATEGY:
  The planner has its own internal timeout at `timeout_s` seconds
  (300s by default). Python's subprocess timeout is set to
  `timeout_s + 15` to give the planner time to finish its internal
  timeout handling, print its [RESULT] and [METRIC] lines, and exit
  cleanly. The Python timeout is a safety net for the rare case
  where the planner hangs beyond its own timeout.
"""

import subprocess
import time
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


# Metric keys that the planner_exec scripts output as [METRIC] lines
METRIC_KEYS = [
    "PlanCost",
    "Runtime_wall_s",
    "Runtime_internal_s",
    "StatesExpanded",
    "StatesGenerated",
    "StatesEvaluated",
    "PeakMemory_KB",
]

# Extra seconds beyond timeout_s for the Python subprocess.
# This buffer allows the planner to complete its internal timeout
# handling and print [RESULT] + [METRIC] lines before Python kills it.
TIMEOUT_BUFFER_SECONDS = 15


def execute_planner(
    planner_name: str,
    docker_image: str,
    domain_path: Path,
    problem_path: Path,
    docker_cfg: dict,
) -> Dict[str, Any]:
    """Run one planner in Docker and return a result dictionary.

    Args:
        planner_name: e.g. "lama", "madagascar"
        docker_image: e.g. "lama_planner"
        domain_path: absolute path to domain.pddl on host
        problem_path: absolute path to instance-XX.pddl on host
        docker_cfg: dict with keys cpus, memory, memory_swap, timeout_seconds

    Returns:
        dict with keys matching CSV_COLUMNS values:
          Output_Status, PlanCost, Runtime_internal_s, Runtime_wall_s,
          StatesExpanded, StatesGenerated, StatesEvaluated, PeakMemoryKB
          plus stdout, stderr for error logging
    """
    # Build the directory strings for the volume mounts
    domain_mount_str = str(domain_path.parent.resolve())
    d_rel = domain_path.name
    
    problem_mount_str = str(problem_path.parent.resolve())
    p_rel = problem_path.name

    timeout_s = docker_cfg.get("timeout_seconds", 300)
    cpus = docker_cfg.get("cpus", "1.0")
    memory = docker_cfg.get("memory", "8g")
    memory_swap = docker_cfg.get("memory_swap", "8g")

    # Python waits longer than the planner's internal timeout so
    # the planner can print its results before Python kills it.
    python_timeout = timeout_s + TIMEOUT_BUFFER_SECONDS

    # Unique container name to enable explicit kill on timeout
    container_name = f"run_{planner_name}_{uuid.uuid4().hex[:8]}"

    # Use two separate volumes
    docker_cmd = [
        "docker", "run",
        "--name", container_name,
        f"--cpus={cpus}",
        f"--memory={memory}",
        f"--memory-swap={memory_swap}",
        "--oom-kill-disable=false",
        "-v", f"{domain_mount_str}:/pddl_domain",
        "-v", f"{problem_mount_str}:/pddl_problem",
        docker_image,
        f"/pddl_domain/{d_rel}",
        f"/pddl_problem/{p_rel}",
    ]

    result = {
        "Output_Status": None,
        "PlanCost": None,
        "Runtime_internal_s": None,
        "Runtime_wall_s": None,
        "StatesExpanded": None,
        "StatesGenerated": None,
        "StatesEvaluated": None,
        "PeakMemoryKB": None,
        # Extra fields for error logging (not written to main CSV)
        "_stdout": "",
        "_stderr": "",
    }

    try:
        start = time.time()
        proc = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=python_timeout,
        )
        wall_time = round(time.time() - start, 6)

        result["_stdout"] = proc.stdout or ""
        result["_stderr"] = proc.stderr or ""
        result["Runtime_wall_s"] = wall_time

        # ----------------------------------------------------------
        # Determine status from the planner's own [RESULT] output
        # ----------------------------------------------------------
        exit_code = proc.returncode

        # First: check for OOM via exit codes / text patterns
        if _is_memout(exit_code, result["_stdout"], result["_stderr"]):
            result["Output_Status"] = "MEMOUT"
            _parse_metrics(result, result["_stdout"])

        # Second: trust the planner's own [RESULT] classification
        elif "[RESULT] STATUS: SUCCESS" in result["_stdout"]:
            result["Output_Status"] = "SUCCESS"
            _parse_metrics(result, result["_stdout"])

        elif "[RESULT] STATUS: MEMOUT" in result["_stdout"]:
            result["Output_Status"] = "MEMOUT"
            _parse_metrics(result, result["_stdout"])

        elif "[RESULT] STATUS: TIMEOUT" in result["_stdout"]:
            result["Output_Status"] = "TIMEOUT"
            result["Runtime_wall_s"] = float(timeout_s)
            _parse_metrics(result, result["_stdout"])

        elif "[RESULT] STATUS: FAILURE" in result["_stdout"]:
            result["Output_Status"] = "FAILURE"
            _parse_metrics(result, result["_stdout"])

        else:
            # No [RESULT] marker at all — container was killed externally
            # (e.g. Ctrl+C, or Docker OOM with no output)
            result["Output_Status"] = "FAILURE"

    except subprocess.TimeoutExpired as e:
        # ----------------------------------------------------------
        # Python safety-net timeout (timeout_s + 15s).
        # This means the planner hung beyond its own internal timeout.
        # Classify as TIMEOUT with the configured timeout value.
        # ----------------------------------------------------------
        result["Runtime_wall_s"] = float(timeout_s)
        result["Output_Status"] = "TIMEOUT"

        # Capture any partial output (may be bytes or str)
        try:
            raw_out = e.stdout
            if isinstance(raw_out, bytes):
                raw_out = raw_out.decode("utf-8", errors="replace")
            result["_stdout"] = raw_out or ""
        except Exception:
            result["_stdout"] = ""

        try:
            raw_err = e.stderr
            if isinstance(raw_err, bytes):
                raw_err = raw_err.decode("utf-8", errors="replace")
            result["_stderr"] = raw_err or ""
        except Exception:
            result["_stderr"] = ""

        # Try to parse any metrics from partial output
        try:
            if result["_stdout"]:
                _parse_metrics(result, result["_stdout"])
        except Exception:
            pass  # Never crash the thread over parsing

        # Kill the still-running container
        try:
            subprocess.run(
                ["docker", "kill", container_name],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    except (FileNotFoundError, ConnectionError, OSError) as exc:
        # Docker daemon is not running or not found
        result["Output_Status"] = "DOCKER_DAEMON_ERROR"
        result["_stderr"] = str(exc)
        # Don't try to remove -- docker may not be available
        return result

    finally:
        # Always clean up the named container (ignore errors)
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    return result


# ======================================================================
# Internal helpers
# ======================================================================

def _is_memout(exit_code: int, stdout: str, stderr: str) -> bool:
    """Detect Out-of-Memory kill from OS signals and text patterns.

    This is the FIRST check before looking at [RESULT] lines.
    It catches cases where Docker's OOM killer terminated the container
    before the planner could print any output.
    """
    if exit_code == 137:  # 128 + SIGKILL(9) -- Linux/Docker OOM killer
        return True
    if exit_code in (21, 22):  # Fast Downward SEARCH_OUT_OF_MEMORY codes
        return True

    combined = (stdout + stderr).lower()
    oom_patterns = [
        "std::bad_alloc",
        "out of memory",
        "memory limit has been reached",
        "search_out_of_memory",
    ]
    return any(pat in combined for pat in oom_patterns)


def _parse_metrics(result: dict, stdout: str) -> None:
    """Extract all [METRIC] lines from planner stdout into the result dict."""
    for line in stdout.splitlines():
        if "[METRIC]" not in line:
            continue

        # Format: "[METRIC] Key: Value"
        after = line.split("[METRIC]", 1)[1].strip()
        if ":" not in after:
            continue

        key, _, raw_value = after.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        # Map shell metric keys to CSV column names
        key_map = {
            "PlanCost": "PlanCost",
            "Runtime_wall_s": "_shell_wall",  # we use Python's measurement
            "Runtime_internal_s": "Runtime_internal_s",
            "StatesExpanded": "StatesExpanded",
            "StatesGenerated": "StatesGenerated",
            "StatesEvaluated": "StatesEvaluated",
            "PeakMemory_KB": "PeakMemoryKB",
        }

        csv_key = key_map.get(key)
        if csv_key is None or csv_key.startswith("_"):
            continue

        # Convert to proper type; treat "N/A" / empty as None
        if raw_value in ("N/A", ""):
            result[csv_key] = None
        elif raw_value == "0.00" and csv_key == "Runtime_internal_s":
            result[csv_key] = None  # Planner didn't report internal time
        else:
            result[csv_key] = _safe_numeric(raw_value)


def _safe_numeric(value: str) -> Any:
    """Convert a string to int or float, or return None on failure."""
    if not value or value == "N/A":
        return None
    try:
        # Try int first (for PlanCost, StatesExpanded, etc.)
        if "." not in value and "e" not in value.lower():
            return int(value)
        return float(value)
    except (ValueError, TypeError):
        return None
