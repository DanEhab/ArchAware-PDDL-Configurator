"""
Heartbeat — Stage 0 Execution Pipeline
=======================================
Background daemon thread that appends a single progress line
to a log file every 60 seconds while the pipeline is active.

Because it is a daemon thread, it automatically dies when
the main thread exits — no cleanup required.
"""

import threading
import time
from pathlib import Path
from datetime import datetime, timezone


class HeartbeatThread(threading.Thread):
    """Background heartbeat that logs pipeline progress every 60 seconds."""

    def __init__(
        self,
        log_path: Path,
        total_runs: int,
        csv_manager,          # reference to the CSVManager instance
        interval: int = 60,
    ):
        super().__init__(daemon=True, name="HeartbeatThread")
        self.log_path = log_path
        self.total_runs = total_runs
        self.csv_manager = csv_manager
        self.interval = interval
        self._stop_event = threading.Event()

        # Updated by worker threads after every completed run
        self.last_completed: str = "N/A"
        self._start_time: float = time.time()

        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main loop — runs until stop() is called or main thread exits."""
        while not self._stop_event.is_set():
            self._write_heartbeat()
            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        """Signal the thread to stop (called from main thread)."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write_heartbeat(self) -> None:
        completed = self.csv_manager.completed_count
        pct = (completed / self.total_runs * 100) if self.total_runs > 0 else 0
        est = self._estimate_remaining(completed)

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = (
            f"[{ts}] "
            f"Last finished: {self.last_completed} | "
            f"Completed: {completed}/{self.total_runs} ({pct:.1f}%) | "
            f"Est. remaining: {est}"
        )

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            # If disk is full, silently skip this heartbeat rather than crash
            pass

    def _estimate_remaining(self, completed: int) -> str:
        """Estimate remaining time based on average pace so far."""
        elapsed = time.time() - self._start_time
        if completed <= 0 or elapsed <= 0:
            return "calculating..."

        remaining_runs = self.total_runs - completed
        avg_per_run = elapsed / completed
        est_seconds = remaining_runs * avg_per_run

        hours = int(est_seconds // 3600)
        minutes = int((est_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
