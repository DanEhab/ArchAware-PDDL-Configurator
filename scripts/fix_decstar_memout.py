"""
Post-Processing Script: Reclassify DecStar MEMOUT -> TIMEOUT
============================================================
DecStar's planner_exec shell script incorrectly mapped exit code 23
(SEARCH_OUT_OF_TIME) to MEMOUT. This script corrects the existing
Stage 0 data by:

1. Updating planner_execution_data.csv: MEMOUT -> TIMEOUT for affected rows
2. Moving error dump files from MEMOUT/ to TIMEOUT/
3. Updating error_register.csv: MEMOUT -> TIMEOUT for affected rows

Only DecStar rows with exitcode 23 (confirmed via dump files) are changed.
"""

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = ROOT / "results" / "planner_execution_data.csv"
ERROR_REG = ROOT / "logs" / "stage0" / "error_register.csv"
MEMOUT_DIR = ROOT / "logs" / "stage0" / "error_dumps" / "MEMOUT"
TIMEOUT_DIR = ROOT / "logs" / "stage0" / "error_dumps" / "TIMEOUT"


def confirm_is_timeout(dump_path: Path) -> bool:
    """Check if a MEMOUT dump file actually contains timeout evidence."""
    if not dump_path.exists():
        return False
    content = dump_path.read_text(encoding="utf-8", errors="replace")
    return "exitcode: 23" in content or "Time limit has been reached" in content


def fix_csv():
    """Reclassify DecStar MEMOUT -> TIMEOUT in the main CSV."""
    rows = []
    changed = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if (row["Planner_Used"] == "decstar"
                    and row["Output_Status"] == "MEMOUT"):
                # Find corresponding dump file
                run_id = row["Run_ID"]
                dump_file = MEMOUT_DIR / f"{run_id}_OOM.txt"
                if confirm_is_timeout(dump_file):
                    row["Output_Status"] = "TIMEOUT"
                    row["Runtime_wall_s"] = "300.0"
                    changed += 1
            rows.append(row)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CSV] Reclassified {changed} rows from MEMOUT -> TIMEOUT")
    return changed


def fix_error_register():
    """Reclassify DecStar MEMOUT -> TIMEOUT in the error register."""
    rows = []
    changed = 0
    with open(ERROR_REG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if (row["Planner"] == "decstar"
                    and row["Error_Type"] == "MEMOUT"):
                run_id = row["Run_ID"]
                dump_file = MEMOUT_DIR / f"{run_id}_OOM.txt"
                if confirm_is_timeout(dump_file):
                    row["Error_Type"] = "TIMEOUT"
                    # Update dump path to reflect new location
                    new_dump = TIMEOUT_DIR / f"{run_id}_TIMEOUT.txt"
                    row["Dump_Path"] = str(new_dump).replace("\\", "/")
                    changed += 1
            rows.append(row)

    with open(ERROR_REG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[REG] Reclassified {changed} rows from MEMOUT -> TIMEOUT")
    return changed


def move_dump_files():
    """Move dump files from MEMOUT/ to TIMEOUT/ with renamed suffix."""
    TIMEOUT_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for dump_file in sorted(MEMOUT_DIR.glob("*_OOM.txt")):
        if confirm_is_timeout(dump_file):
            run_id = dump_file.name.split("_")[0]
            new_name = f"{run_id}_TIMEOUT.txt"
            new_path = TIMEOUT_DIR / new_name

            # Also update the content header
            content = dump_file.read_text(encoding="utf-8", errors="replace")
            content = content.replace("Error Type: MEMOUT", "Error Type: TIMEOUT")
            new_path.write_text(content, encoding="utf-8")

            dump_file.unlink()
            moved += 1
            print(f"  Moved: {dump_file.name} -> TIMEOUT/{new_name}")

    print(f"[DUMPS] Moved {moved} files from MEMOUT/ -> TIMEOUT/")
    return moved


def verify():
    """Verify the reclassification is correct."""
    # Check CSV
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    decstar_memout = [r for r in reader if r["Planner_Used"] == "decstar" and r["Output_Status"] == "MEMOUT"]
    decstar_timeout = [r for r in reader if r["Planner_Used"] == "decstar" and r["Output_Status"] == "TIMEOUT"]

    print(f"\n=== Verification ===")
    print(f"DecStar MEMOUT remaining: {len(decstar_memout)} (expected: 0)")
    print(f"DecStar TIMEOUT total: {len(decstar_timeout)} (expected: 40)")

    # Check dump directories
    memout_files = list(MEMOUT_DIR.glob("*.txt")) if MEMOUT_DIR.exists() else []
    timeout_files = list(TIMEOUT_DIR.glob("*.txt")) if TIMEOUT_DIR.exists() else []
    print(f"MEMOUT dump files: {len(memout_files)} (expected: 0)")
    print(f"TIMEOUT dump files: {len(timeout_files)} (expected: 88 + 40 = 128)")

    # Totals
    from collections import Counter
    status_counts = Counter(r["Output_Status"] for r in reader)
    print(f"\nNew global totals:")
    for status in ["SUCCESS", "TIMEOUT", "MEMOUT", "FAILURE"]:
        print(f"  {status}: {status_counts.get(status, 0)}")

    assert len(decstar_memout) == 0, "FAIL: DecStar still has MEMOUT entries"
    assert len(memout_files) == 0, "FAIL: MEMOUT dump files still exist"
    print("\n✅ All checks passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Post-Processing: DecStar MEMOUT -> TIMEOUT Reclassification")
    print("=" * 60)
    print()

    csv_changed = fix_csv()
    reg_changed = fix_error_register()
    dumps_moved = move_dump_files()

    print()
    verify()
