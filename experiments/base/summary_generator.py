"""
Summary Generator — Stage 0 Execution Pipeline
================================================
Generates a human-readable markdown summary whenever the
pipeline halts (clean exit, Ctrl+C, or system error).

Files are written to  logs/stage0/run_summaries/run_summary_N.md
with an auto-incrementing counter.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


class SummaryGenerator:
    """Generates post-run markdown summaries."""

    def __init__(self, summaries_dir: Path, csv_path: Path, total_runs: int, stage_name: str = "Stage 0 (BASELINE)"):
        self.summaries_dir = summaries_dir
        self.csv_path = csv_path
        self.total_runs = total_runs
        self.stage_name = stage_name
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        cause: str,
        elapsed_seconds: float,
        error_count: int = 0,
    ) -> Path:
        """Create a run_summary_N.md file and return its path.

        Args:
            cause: Termination reason (CLEAN_EXIT, SIGINT, SYSTEM_ERROR, …)
            elapsed_seconds: Total wall-clock time of this run session
            error_count: Number of errors logged to the error register
        """
        summary_number = self._next_summary_number()
        summary_path = self.summaries_dir / f"run_summary_{summary_number}.md"

        # Read the CSV to build aggregate stats
        stats = self._aggregate_stats()
        completed = sum(
            sum(counts.values()) for counts in stats.values()
        )

        # Format elapsed time
        hrs = int(elapsed_seconds // 3600)
        mins = int((elapsed_seconds % 3600) // 60)
        secs = int(elapsed_seconds % 60)

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        lines = [
            f"# Run Summary #{summary_number} — {self.stage_name}",
            f"**Generated**: {ts}",
            f"**Termination Cause**: {cause}",
            "",
            "## Aggregate Results",
            "",
            "| Planner | SUCCESS | TIMEOUT | MEMOUT | FAILURE | Total |",
            "|---------|---------|---------|--------|---------|-------|",
        ]

        planners_order = ["lama", "decstar", "bfws", "madagascar"]
        for p in planners_order:
            counts = stats.get(p, {})
            s = counts.get("SUCCESS", 0)
            t = counts.get("TIMEOUT", 0)
            m = counts.get("MEMOUT", 0)
            f = counts.get("FAILURE", 0)
            total = s + t + m + f
            lines.append(
                f"| {p:<9} | {s:<7} | {t:<7} | {m:<6} | {f:<7} | {total:<5} |"
            )

        lines.extend([
            "",
            "## Timing",
            f"- Total elapsed time: {hrs}h {mins}m {secs}s",
            f"- Runs completed: {completed}/{self.total_runs}",
            f"- Errors logged: {error_count}",
        ])

        summary_path.write_text("\n".join(lines), encoding="utf-8")
        return summary_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_summary_number(self) -> int:
        """Find the next available run_summary_N.md number."""
        existing = list(self.summaries_dir.glob("run_summary_*.md"))
        if not existing:
            return 1
        numbers = []
        for p in existing:
            try:
                n = int(p.stem.replace("run_summary_", ""))
                numbers.append(n)
            except ValueError:
                pass
        return max(numbers, default=0) + 1

    def _aggregate_stats(self) -> dict:
        """Read the CSV and tally SUCCESS/TIMEOUT/MEMOUT/FAILURE per planner."""
        stats: dict = defaultdict(lambda: defaultdict(int))

        if not self.csv_path.exists():
            return stats

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                planner = row.get("Planner_Used", "unknown")
                status = row.get("Output_Status", "FAILURE")
                stats[planner][status] += 1

        return stats
