"""
Error Handler -- Stage 0 Execution Pipeline
===========================================
Dual-mechanism error logging:
  A) Error Register CSV  -- tabular index of every non-SUCCESS outcome
  B) Error Dumps         -- verbose stdout/stderr text files organised
                            into subfolders by error type (TIMEOUT/
                            MEMOUT/ FAILURE/)

Thread-safe: uses its own lock for concurrent writes from
the 4 planner threads.
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
    "Error_Type",
    "Dump_Path",
]


class ErrorHandler:
    """Thread-safe error logging to CSV register and text dump files."""

    def __init__(self, error_register_path: Path, error_dumps_dir: Path):
        self.register_path = error_register_path
        self.dumps_dir = error_dumps_dir
        self._lock = threading.Lock()

        # Create directories
        self.register_path.parent.mkdir(parents=True, exist_ok=True)
        self.dumps_dir.mkdir(parents=True, exist_ok=True)

        # Create subfolders for each error type
        for subdir in ("TIMEOUT", "MEMOUT", "FAILURE"):
            (self.dumps_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Write CSV header if file doesn't exist yet
        if not self.register_path.exists():
            with open(self.register_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ERROR_REGISTER_COLUMNS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_planner_error(
        self,
        run_id: int,
        domain: str,
        problem: str,
        planner: str,
        error_type: str,
        stdout: str,
        stderr: str,
    ) -> None:
        """Log a planner error (TIMEOUT, MEMOUT, FAILURE).

        Saves a verbose dump file into the appropriate subfolder
        and appends a row to the register CSV.
        """
        dump_path = self._save_error_dump(run_id, error_type, stdout, stderr)

        self._append_register_row(
            component="PLANNER",
            run_id=run_id,
            domain=domain,
            problem=problem,
            planner=planner,
            error_type=error_type,
            dump_path=str(dump_path),
        )

    def log_system_error(
        self,
        error_type: str,
        error_message: str,
        domain: str = "N/A",
        problem: str = "N/A",
        planner: str = "N/A",
        run_id: int = -1,
    ) -> None:
        """Log a system-level error (DOCKER_DAEMON, DISK_FULL)."""
        self._append_register_row(
            component="SYSTEM",
            run_id=run_id,
            domain=domain,
            problem=problem,
            planner=planner,
            error_type=error_type,
            dump_path="N/A",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save_error_dump(
        self, run_id: int, error_type: str, stdout: str, stderr: str
    ) -> Path:
        """Save verbose stdout+stderr to a text dump file in the
        appropriate error-type subfolder."""
        suffix_map = {
            "MEMOUT": "OOM",
            "FAILURE": "CRASH",
            "TIMEOUT": "TIMEOUT",
            "INVALID_OUTPUT": "INVALID_OUTPUT",
        }
        suffix = suffix_map.get(error_type, error_type)

        # Place into subfolder: error_dumps/TIMEOUT/214_TIMEOUT.txt
        subfolder = self.dumps_dir / error_type
        subfolder.mkdir(parents=True, exist_ok=True)
        dump_file = subfolder / f"{run_id}_{suffix}.txt"

        content_parts = [
            f"=== ERROR DUMP -- Run ID {run_id} ===",
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

    def _append_register_row(self, **kwargs) -> None:
        """Thread-safe append of a single row to the error register CSV."""
        row = {
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Component": kwargs.get("component", "UNKNOWN"),
            "Run_ID": kwargs.get("run_id", -1),
            "Domain": kwargs.get("domain", "N/A"),
            "Problem": kwargs.get("problem", "N/A"),
            "Planner": kwargs.get("planner", "N/A"),
            "Error_Type": kwargs.get("error_type", "UNKNOWN"),
            "Dump_Path": kwargs.get("dump_path", "N/A"),
        }

        with self._lock:
            with open(
                self.register_path, "a", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(f, fieldnames=ERROR_REGISTER_COLUMNS)
                writer.writerow(row)
