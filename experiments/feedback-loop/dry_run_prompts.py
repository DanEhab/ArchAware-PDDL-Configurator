import os
import sys
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

sys.path.insert(0, str(REPO_ROOT / "experiments" / "feedback-loop"))

from run_stage3 import resolve_seed_domain

def print_separator(title):
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def test_dry_run():
    print_separator("SCENARIO 6A: TokenLimitExceeded (depots | Gemini 3.1 Pro | DecStar)")
    seed_path, stage0, hist, tel, ipc, is_valid = resolve_seed_domain("depots", "decstar", "gemini-3.1-pro")
    print("=== HISTORY BUFFER ===")
    for h in hist: print(h)
    print("\n=== TELEMETRY FEEDBACK ===")
    print(str(tel)[:500] + "\n... [DOMAIN TRUNCATED FOR DRY RUN PRINTING]\n")

    print_separator("SCENARIO 6C: V4 Semantic Failure (ricochet-robots | GPT-5.4 | LAMA)")
    seed_path, stage0, hist, tel, ipc, is_valid = resolve_seed_domain("ricochet-robots", "lama", "gpt-5.4")
    print("=== HISTORY BUFFER ===")
    for h in hist: print(h)
    print("\n=== TELEMETRY FEEDBACK ===")
    print(str(tel)[:500] + "\n... [DOMAIN TRUNCATED FOR DRY RUN PRINTING]\n")

    print_separator("SCENARIO 6B: Valid Domain (barman | GPT-5.4 | LAMA)")
    seed_path, stage0, hist, tel, ipc, is_valid = resolve_seed_domain("barman", "lama", "gpt-5.4")
    print("=== HISTORY BUFFER ===")
    for h in hist: print(h)
    print("\n=== TELEMETRY FEEDBACK ===")
    if tel == "DELAY_VALID_TELEMETRY":
        print("TELEMETRY IS DELAYED UNTIL RUNTIME FOR VALID DOMAINS TO COMBINE BASELINE AND ITER0 SCORE")
    else:
        print(str(tel)[:500] + "\n... [DOMAIN TRUNCATED FOR DRY RUN PRINTING]\n")

if __name__ == "__main__":
    test_dry_run()