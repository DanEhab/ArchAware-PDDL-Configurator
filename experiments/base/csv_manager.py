"""
CSV Manager — Stage 0 Execution Pipeline
=========================================
Thread-safe CSV writer with built-in checkpointing.

On init: loads any existing CSV, builds an O(1) lookup set
of completed runs, and determines the next Run_ID.

All public methods are protected by a threading.Lock so
four concurrent planner threads can safely call append_row().
"""

import threading
import csv
from pathlib import Path

# Canonical column order — must match the Execution Protocol §2.1
CSV_COLUMNS = [
    "Run_ID",
    "Domain_Name",
    "Domain_File",
    "Problem_Instance",
    "Planner_Used",
    "Stage",
    "LLM_Used",
    "PromptID",
    "PlanCost",
    "Runtime_internal_s",
    "Runtime_wall_s",
    "Output_Status",
    "StatesExpanded",
    "StatesGenerated",
    "StatesEvaluated",
    "PeakMemoryKB",
    "Timestamp",
]


class CSVManager:
    """Thread-safe CSV manager with O(1) checkpoint lookups."""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self._lock = threading.Lock()
        self.completed_runs: set = set()  # (domain, problem, planner)
        self.next_id: int = 1
        self._load_existing()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _load_existing(self) -> None:
        """Load existing CSV and populate the completed_runs set."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.csv_path.exists():
            # Write header for a fresh file
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_COLUMNS)
            return

        max_id = 0
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (
                    row.get("Domain_Name", ""),
                    row.get("Problem_Instance", ""),
                    row.get("Planner_Used", ""),
                )
                self.completed_runs.add(key)
                try:
                    rid = int(row.get("Run_ID", 0))
                    if rid > max_id:
                        max_id = rid
                except (ValueError, TypeError):
                    pass
        self.next_id = max_id + 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_completed(self, domain: str, problem: str, planner: str) -> bool:
        """O(1) check whether this run already exists in the CSV."""
        return (domain, problem, planner) in self.completed_runs

    def append_row(self, row_data: dict) -> int:
        """Thread-safe append of a single result row.

        Assigns the next Run_ID, writes to CSV, and updates the
        completed_runs set.  Returns the assigned Run_ID.
        """
        with self._lock:
            run_id = self.next_id
            self.next_id += 1

            row_data["Run_ID"] = run_id

            # Ensure every column is present (write None as empty string)
            ordered = []
            for col in CSV_COLUMNS:
                val = row_data.get(col)
                ordered.append("" if val is None else val)

            with open(
                self.csv_path, "a", newline="", encoding="utf-8"
            ) as f:
                writer = csv.writer(f)
                writer.writerow(ordered)

            # Update checkpoint set
            self.completed_runs.add(
                (
                    row_data.get("Domain_Name", ""),
                    row_data.get("Problem_Instance", ""),
                    row_data.get("Planner_Used", ""),
                )
            )
            return run_id

    @property
    def completed_count(self) -> int:
        """Number of runs that have been written so far."""
        return len(self.completed_runs)
