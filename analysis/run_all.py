"""
Master Analysis Runner
======================
Runs all stage analysis scripts in sequence.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "stage0_analysis.py",
    "stage1_analysis.py",
    "stage2_analysis.py",
    "stage3_analysis.py",
]

def main():
    script_dir = Path(__file__).resolve().parent
    
    for script in SCRIPTS:
        path = script_dir / script
        if not path.exists():
            print(f"⚠ Script not found: {script}")
            continue
        
        print("\n" + "═" * 70)
        print(f"  Running: {script}")
        print("═" * 70 + "\n")
        
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(script_dir.parent),
            capture_output=False,
        )
        
        if result.returncode != 0:
            print(f"\n❌ {script} exited with code {result.returncode}")
        else:
            print(f"\n✅ {script} completed successfully")
    
    print("\n" + "═" * 70)
    print("  All analysis scripts completed!")
    print("═" * 70)


if __name__ == "__main__":
    main()
