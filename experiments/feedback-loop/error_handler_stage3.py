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
from csv_manager_stage3 import _normalise_llm_name  # type: ignore

# Columns for the planner error register CSV
PLANNER_ERROR_COLUMNS = [
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

# Columns for the LLM error register CSV (no Problem column)
LLM_ERROR_COLUMNS = [
    "Timestamp",
    "Component",
    "Domain",
    "Planner",
    "LLM",
    "Iteration",
    "Error_Type",
    "Dump_Path",
]


class ErrorHandlerStage3:
    """Thread-safe error logging to CSV register and text dump files."""

    def __init__(self, error_register_path: Path, error_dumps_dir: Path,
                 is_llm_handler: bool = False):
        self.register_path = error_register_path
        self.dumps_dir = error_dumps_dir
        self.is_llm_handler = is_llm_handler
        self._lock = threading.Lock()

        # Create directories
        self.register_path.parent.mkdir(parents=True, exist_ok=True)
        self.dumps_dir.mkdir(parents=True, exist_ok=True)

        # For planner errors, create subfolders for each error type
        if not is_llm_handler:
            for subdir in ("TIMEOUT", "MEMOUT", "FAILURE"):
                (self.dumps_dir / subdir).mkdir(parents=True, exist_ok=True)
        # LLM errors: flat structure (no sub-folders)

        # Determine which column set to use
        columns = LLM_ERROR_COLUMNS if is_llm_handler else PLANNER_ERROR_COLUMNS

        # Write CSV header if file doesn't exist yet
        if not self.register_path.exists():
            with open(self.register_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)

    def log_planner_error(
        self,
        run_id: int,
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
        canonical_llm = _normalise_llm_name(llm)
        dump_path = self._save_error_dump(str(run_id), error_type, stdout, stderr)

        self._append_planner_row(
            run_id=run_id,
            domain=domain,
            problem=problem,
            planner=planner,
            llm=canonical_llm,
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
        canonical_llm = _normalise_llm_name(llm)
        # Run_ID is the canonical LLM name
        run_id = canonical_llm
        dump_path = self._save_llm_error_dump(
            f"{domain}_{planner}_{canonical_llm}_iter{iteration}",
            error_type, prompt_text, error_message
        )

        self._append_llm_row(
            domain=domain,
            planner=planner,
            llm=canonical_llm,
            iteration=iteration,
            error_type=error_type,
            dump_path=str(dump_path),
        )

    def _save_error_dump(
        self, run_id: str, error_type: str, stdout: str, stderr: str
    ) -> Path:
        """Save verbose stdout+stderr to a text dump file (planner errors use sub-folders)."""
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
        """Save LLM error details to a text dump file (flat — no sub-folders).
        Full prompt and error message are saved without truncation."""
        # Flat structure: save directly in dumps_dir
        dump_file = self.dumps_dir / f"{run_id}_{error_type}.txt"

        content_parts = [
            f"=== LLM ERROR DUMP -- {run_id} ===",
            f"Error Type: {error_type}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "",
            "=== FULL PROMPT ===",
            prompt_text if prompt_text else "(empty)",
            "",
            "=== FULL ERROR MESSAGE ===",
            error_message if error_message else "(empty)",
        ]

        dump_file.write_text("\n".join(content_parts), encoding="utf-8")
        return dump_file

    def _append_planner_row(self, **kwargs) -> None:
        """Thread-safe append of a planner error row to the CSV register."""
        row = {
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Component": "PLANNER",
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
                writer = csv.DictWriter(f, fieldnames=PLANNER_ERROR_COLUMNS)
                writer.writerow(row)

    def _append_llm_row(self, **kwargs) -> None:
        """Thread-safe append of an LLM error row to the CSV register (no Problem column)."""
        row = {
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Component": "LLM_API",
            "Domain": kwargs.get("domain", "N/A"),
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
                writer = csv.DictWriter(f, fieldnames=LLM_ERROR_COLUMNS)
                writer.writerow(row)
