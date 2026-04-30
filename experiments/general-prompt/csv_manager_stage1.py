"""
CSV Manager — Stage 1 Execution Pipeline
=========================================
Thread-safe CSV writer with built-in checkpointing for Stage 1.

Writes identically to TWO CSV files:
1. The global planner_execution_data.csv
2. The local general_planner_execution_data.csv

Checkpointing checks `(domain, problem, planner, llm_used)` to
ensure uniqueness for each LLM configuration.
"""

import threading
import csv
from pathlib import Path

# Canonical column order
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


class CSVManagerStage1:
    """Thread-safe CSV manager writing to two files with O(1) lookups."""

    def __init__(self, global_csv_path: Path, local_csv_path: Path):
        self.global_csv_path = global_csv_path
        self.local_csv_path = local_csv_path
        self._lock = threading.Lock()
        
        # Checkpoint key: (domain, problem, planner, llm_used)
        self.completed_runs: set = set()
        self.next_id: int = 1
        
        self._load_existing()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _load_existing(self) -> None:
        """Load existing global CSV and populate the completed_runs set."""
        self.global_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize global if missing
        if not self.global_csv_path.exists():
            with open(self.global_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_COLUMNS)

        # Initialize local if missing
        if not self.local_csv_path.exists():
            with open(self.local_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_COLUMNS)

        max_id = 0
        with open(self.global_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only add Stage 1 (General) runs to the checkpoint set
                if row.get("Stage") == "General":
                    key = (
                        row.get("Domain_Name", ""),
                        row.get("Problem_Instance", ""),
                        row.get("Planner_Used", ""),
                        row.get("LLM_Used", "N/A"),
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

    def is_completed(self, domain: str, problem: str, planner: str, llm_used: str) -> bool:
        """O(1) check whether this specific run already exists in the CSV."""
        return (domain, problem, planner, llm_used) in self.completed_runs

    def append_row(self, row_data: dict) -> int:
        """Thread-safe append of a single result row to both CSVs."""
        with self._lock:
            run_id = self.next_id
            self.next_id += 1

            row_data["Run_ID"] = run_id

            ordered = []
            for col in CSV_COLUMNS:
                val = row_data.get(col)
                ordered.append("N/A" if val is None else val)

            # Write to Global
            with open(self.global_csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ordered)
                
            # Write to Local
            with open(self.local_csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ordered)

            # Update checkpoint set
            self.completed_runs.add(
                (
                    row_data.get("Domain_Name", ""),
                    row_data.get("Problem_Instance", ""),
                    row_data.get("Planner_Used", ""),
                    row_data.get("LLM_Used", "N/A"),
                )
            )
            return run_id

    @property
    def completed_count(self) -> int:
        """Number of runs loaded/completed."""
        return len(self.completed_runs)
