"""
Error Handler -- Stage 3 Feedback Loop
=======================================
Dual-mechanism error logging following the same pattern
as experiments/base/error_handler.py:
  A) Error Register CSV  -- tabular index of every error
  B) Error Dumps         -- verbose stdout/stderr text files

Two separate error handler instances:
  1. Planner errors → logs/stage3/error_register.csv + logs/stage3/error_dumps/
  2. LLM API errors → logs/stage3/LLM_run/error_register.csv + logs/stage3/LLM_run/error_dumps/

Thread-safe: uses its own lock for concurrent writes from
the 4 LLM pipeline threads.
"""

import threading
import csv
from pathlib import Path
from datetime import datetime, timezone

# Columns for the error register CSV
ERROR_REGISTER_COLUMNS = [
    "Timestamp",
    "Component",
    "Run_ID",
    "Domain",
    "Problem",
    "Planner",
    "LLM",
    "Iteration",
    "Error_Type",
    "Dump_Path",
]


class ErrorHandlerStage3:
    """Thread-safe error logging to CSV register and text dump files."""

    def __init__(self, error_register_path: Path, error_dumps_dir: Path):
        self.register_path = error_register_path
        self.dumps_dir = error_dumps_dir
        self._lock = threading.Lock()

        # Create directories
        self.register_path.parent.mkdir(parents=True, exist_ok=True)
        self.dumps_dir.mkdir(parents=True, exist_ok=True)

        # Create subfolders for each error type
        for subdir in ("TIMEOUT", "MEMOUT", "FAILURE", "LLM_API"):
            (self.dumps_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Write CSV header if file doesn't exist yet
        if not self.register_path.exists():
            with open(self.register_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ERROR_REGISTER_COLUMNS)

    def log_planner_error(
        self,
        domain: str,
        problem: str,
        planner: str,
        llm: str,
        iteration: int,
        error_type: str,
        stdout: str,
        stderr: str,
    ) -> None:
        """Log a planner error (TIMEOUT, MEMOUT, FAILURE)."""
        run_id = f"{domain}_{planner}_{llm}_iter{iteration}_{problem}"
        dump_path = self._save_error_dump(run_id, error_type, stdout, stderr)

        self._append_register_row(
            component="PLANNER",
            run_id=run_id,
            domain=domain,
            problem=problem,
            planner=planner,
            llm=llm,
            iteration=iteration,
            error_type=error_type,
            dump_path=str(dump_path),
        )

    def log_llm_error(
        self,
        domain: str,
        planner: str,
        llm: str,
        iteration: int,
        error_type: str,
        prompt_text: str,
        error_message: str,
    ) -> None:
        """Log an LLM API error."""
        run_id = f"{domain}_{planner}_{llm}_iter{iteration}"
        dump_path = self._save_llm_error_dump(
            run_id, error_type, prompt_text, error_message
        )

        self._append_register_row(
            component="LLM_API",
            run_id=run_id,
            domain=domain,
            problem="N/A",
            planner=planner,
            llm=llm,
            iteration=iteration,
            error_type=error_type,
            dump_path=str(dump_path),
        )

    def _save_error_dump(
        self, run_id: str, error_type: str, stdout: str, stderr: str
    ) -> Path:
        """Save verbose stdout+stderr to a text dump file."""
        subfolder = self.dumps_dir / error_type
        subfolder.mkdir(parents=True, exist_ok=True)
        dump_file = subfolder / f"{run_id}_{error_type}.txt"

        content_parts = [
            f"=== ERROR DUMP -- {run_id} ===",
            f"Error Type: {error_type}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "",
            "=== STDOUT ===",
            stdout if stdout else "(empty)",
            "",
            "=== STDERR ===",
            stderr if stderr else "(empty)",
        ]

        dump_file.write_text("\n".join(content_parts), encoding="utf-8")
        return dump_file

    def _save_llm_error_dump(
        self, run_id: str, error_type: str, prompt_text: str, error_message: str
    ) -> Path:
        """Save LLM error details to a text dump file."""
        subfolder = self.dumps_dir / "LLM_API"
        subfolder.mkdir(parents=True, exist_ok=True)
        dump_file = subfolder / f"{run_id}_{error_type}.txt"

        content_parts = [
            f"=== LLM ERROR DUMP -- {run_id} ===",
            f"Error Type: {error_type}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "",
            "=== PROMPT (first 2000 chars) ===",
            prompt_text[:2000] if prompt_text else "(empty)",
            "",
            "=== ERROR MESSAGE ===",
            error_message if error_message else "(empty)",
        ]

        dump_file.write_text("\n".join(content_parts), encoding="utf-8")
        return dump_file

    def _append_register_row(self, **kwargs) -> None:
        """Thread-safe append of a single row to the error register CSV."""
        row = {
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Component": kwargs.get("component", "UNKNOWN"),
            "Run_ID": kwargs.get("run_id", "N/A"),
            "Domain": kwargs.get("domain", "N/A"),
            "Problem": kwargs.get("problem", "N/A"),
            "Planner": kwargs.get("planner", "N/A"),
            "LLM": kwargs.get("llm", "N/A"),
            "Iteration": kwargs.get("iteration", -1),
            "Error_Type": kwargs.get("error_type", "UNKNOWN"),
            "Dump_Path": kwargs.get("dump_path", "N/A"),
        }

        with self._lock:
            with open(
                self.register_path, "a", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(f, fieldnames=ERROR_REGISTER_COLUMNS)
                writer.writerow(row)
