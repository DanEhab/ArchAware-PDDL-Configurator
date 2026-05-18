import os
import sys
import glob
import concurrent.futures
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Handle directory with hyphen
sys.path.insert(0, str(REPO_ROOT / "experiments" / "feedback-loop"))

from loop_engine import run_feedback_loop  # type: ignore
from meta_controller import build_telemetry_for_valid_full, get_6A_telemetry, get_6C_telemetry  # type: ignore

DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
PLANNERS = ["lama", "decstar", "bfws", "madagascar"]
LLMS = ["claude-opus-4.6", "deepseek-r1", "gemini-3.1-pro", "gpt-5.4", "gpt-5.4-2026-03-05"]

def get_test_instances(domain):
    indices = [1, 2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19]
    domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmarks", domain)
    if not os.path.exists(domain_benchmark_dir):
        domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmark_samples", domain)
    all_files = glob.glob(os.path.join(domain_benchmark_dir, "**", "*.pddl"), recursive=True)
    test_instances = []
    for f in all_files:
        name = os.path.basename(f)
        if name == "domain.pddl": continue
        num_str = ''.join(filter(str.isdigit, name))
        if num_str and int(num_str) in indices:
            test_instances.append(f)
    return sorted(list(set(test_instances)))

def resolve_seed_domain(domain, planner, llm):
    # This enforces Point 6: Iteration 1 Routing.
    stage0_path = os.path.join(REPO_ROOT, "benchmarks", domain, "domain.pddl")
    if not os.path.exists(stage0_path):
        stage0_path = os.path.join(REPO_ROOT, "benchmark_samples", domain, "domain.pddl")
    
    with open(stage0_path, 'r', encoding='utf-8') as f:
        baseline_pddl = f.read()

    # Look up in LLM Gen Data
    gen_csv = os.path.join(REPO_ROOT, "results", "arch_aware", "LLM Results", "arch_aware_llm_generation_data.csv")
    
    # Defaults
    is_valid_seed = False
    seed_domain_path = stage0_path
    init_hist = []
    init_tel = ""
    stage2_ipc = 0.0 # Will be 0.0 unless valid
    
    if os.path.exists(gen_csv):
        df = pd.read_csv(gen_csv)
        PROMPT_ID_MAP = {"lama":1, "decstar":2, "bfws":3, "madagascar":4}
        pid = PROMPT_ID_MAP.get(planner, 1)
        
        # Match llm via contains (since string names vary: gpt-5.4 vs gpt-5.4-2026-03-05)
        llm_search = llm
        if 'gpt' in llm.lower() and '5.4' in llm:
            llm_search = 'gpt-5.4'
            
        match = df[(df['Domain Name'] == domain) & (df['Prompt ID'] == pid) & (df['LLM Model'].str.contains(llm_search))]
        
        if match.empty:
            # 6A: Not in CSV -> likely API failure
            init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — Unknown API Error.\n  • No valid PDDL domain was produced."]
            init_tel = get_6A_telemetry("Unknown API Error", baseline_pddl)
        else:
            row = match.iloc[0]
            val_status = str(row['Validation Status'])
            llm_status = str(row['LLM_Status'])
            v4_pass = str(row['Passed V4'])
            
            if 'tokenlimit' in llm_status.lower() or val_status == 'TokenLimitExceeded':
                # 6A-i TokenLimit
                init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — Your response exceeded the maximum token output\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("TokenLimitExceeded", baseline_pddl)
            elif val_status == 'VALID' and row['Passed Stage V1'] == True and v4_pass == "True":
                # 6B: Valid Domain
                is_valid_seed = True
                extracted_path = str(row['Path to Extracted PDDL'])
                if os.path.exists(extracted_path):
                    seed_domain_path = extracted_path
                else:
                    seed_domain_path = stage0_path # fallback just in case
                
                init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • No rationale was recorded for this attempt."]
                
                imp_csv = os.path.join(REPO_ROOT, "results", "arch_aware", "improvement", "improvement_results.csv")
                init_tel = build_telemetry_for_valid_full(domain, planner, llm, imp_csv)
                
                # Best score gets set to Stage 2 IPC (approx logic: we lookup real later)
                stage2_ipc = 1.0 # placeholder for valid IPC, will be overwritten by point 5
            else:
                # 6C: Invalid Domain
                error_str = str(row['VAL_error_string']) if pd.notna(row['VAL_error_string']) else "Unknown semantic violation"
                failed_str = "V4" if v4_pass == "False" else "V2"
                init_hist = [f"PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — {failed_str} Check"]
                init_tel = get_6C_telemetry(failed_str, error_str, baseline_pddl)
                
    return seed_domain_path, stage0_path, init_hist, init_tel, stage2_ipc, is_valid_seed

def run_pipeline_for_llm(llm):
    print(f"=== Starting Pipeline for LLM: {llm} ===")
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    os.makedirs(output_dir, exist_ok=True)
    
    for domain in DOMAINS:
        test_instances = get_test_instances(domain)
        if not test_instances: continue
            
        for planner in PLANNERS:
            try:
                seed_domain_path, stage0_baseline_path, init_hist, init_tel, stage2_ipc, is_valid_seed = resolve_seed_domain(domain, planner, llm)
                
                run_feedback_loop(
                    domain_name=domain,
                    planner_name=planner,
                    llm_model=llm,
                    base_domain_path=seed_domain_path,
                    test_instances=test_instances,
                    output_dir=output_dir,
                    stage0_baseline_path=stage0_baseline_path,
                    initial_history_buffer=init_hist,
                    initial_telemetry_feedback=init_tel,
                    stage2_best_score=stage2_ipc,
                    is_valid_seed=is_valid_seed,
                    max_iter=3
                )
            except Exception as e:
                print(f"Error processing {domain} | {planner} | {llm}: {e}")

def main():
    print("Starting Stage 3 Feedback Loop Master Orchestrator...")
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    os.makedirs(output_dir, exist_ok=True)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_pipeline_for_llm, llm): llm for llm in LLMS}
        for future in concurrent.futures.as_completed(futures):
            llm = futures[future]
            try:
                future.result()
                print(f"Pipeline finished successfully for {llm}")
            except Exception as e:
                print(f"Pipeline crashed for {llm}: {e}")

if __name__ == "__main__":
    main()
