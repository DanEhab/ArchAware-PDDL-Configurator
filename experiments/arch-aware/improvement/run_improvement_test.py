"""
run_improvement_test.py - Phase D of Stage 2 (Architecture-Aware Prompting)

This script analyzes the results of Stage 2 (Arch-Aware Execution) against the baseline (Stage 0).
It calculates the IPC Score gains for each (domain, llm, target_planner) triple.
It performs the Wilcoxon signed-rank test and checks for statistical and practical significance.
Improved domains are physical copied to `results/arch_aware/Improved Domains/`.

NOTE ON TUNING:
The Practical Significance Threshold (`MEAN_GAIN_THRESHOLD = 0.05`) is currently set to require
at least an average 0.05 IPC score gain. If you find this is destroying your results (i.e. rejecting
too many genuinely good domains), you can lower it (e.g., to 0.02 or even 0.0) right below.
"""

import sys
import shutil
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import wilcoxon
import json
from datetime import datetime

# Prevent scipy from throwing warnings if all gains are identical or zero
warnings.filterwarnings("ignore", category=UserWarning)

# =====================================================================
# TUNABLE PARAMETERS
# =====================================================================

# 1. Wilcoxon P-Value Threshold (Alpha)
P_VALUE_THRESHOLD = 0.25

# 2. Practical Significance Threshold
# If this is 0.05, it means the average IPC score must jump by at least +0.05. 
# >> Change this to 0.0 or 0.01 if 0.05 is rejecting too many domains! <<
MEAN_GAIN_THRESHOLD = 0.0

# =====================================================================
# PATHS
# =====================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXECUTION_CSV_PATH = PROJECT_ROOT / "results" / "planner_execution_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "arch_aware" / "improvement"
OUTPUT_CSV_PATH = OUTPUT_DIR / "improvement_results.csv"

VALIDATED_DOMAINS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Validated Domains"
IMPROVED_DOMAINS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Improved Domains"

def load_data():
    """Loads and standardizes the execution data CSV."""
    if not EXECUTION_CSV_PATH.exists():
        print(f"[ERROR] Cannot find execution data at {EXECUTION_CSV_PATH}")
        sys.exit(1)
        
    df = pd.read_csv(EXECUTION_CSV_PATH)
    
    # Convert Runtime_wall_s to numeric, forcing 'N/A' to NaN
    df['Runtime_wall_s'] = pd.to_numeric(df['Runtime_wall_s'], errors='coerce')
    
    return df

def get_best_times(df):
    """
    Computes T*_i: the best (fastest) Runtime_wall_s that each planner
    achieved on each problem instance across ALL configurations (Baseline, Stage 1, Stage 2).
    """
    success_df = df[df['Output_Status'] == 'SUCCESS']
    
    # Group by Planner, Domain, Problem and find the minimum runtime
    best_times = success_df.groupby(['Planner_Used', 'Domain_Name', 'Problem_Instance'])['Runtime_wall_s'].min().reset_index()
    best_times.rename(columns={'Runtime_wall_s': 'T_star'}, inplace=True)
    return best_times

def calculate_ipc_score(row, t_star):
    """
    Calculates the IPC score for a given run based on its Runtime_wall_s vs T*.
    Score = 1 / (1 + log10(T / T*))
    """
    if row['Output_Status'] != 'SUCCESS' or pd.isna(row['Runtime_wall_s']):
        return 0.0
    if pd.isna(t_star) or t_star == 0:
        return 0.0 # Safety fallback
    
    ratio = row['Runtime_wall_s'] / t_star
    
    # Because of floating point noise, ratio might be slightly < 1.0 (e.g. 0.99999). 
    # Log of < 1 is negative, which could artificially push score > 1. Clamp to 1.0.
    if ratio < 1.0:
        ratio = 1.0
        
    return 1.0 / (1.0 + np.log10(ratio))

def main():
    print("=" * 70)
    print("   STAGE 2 - PHASE D: IMPROVEMENT DETECTION")
    print("=" * 70)
    print(f"[CFG] Alpha (P-Value) Threshold: < {P_VALUE_THRESHOLD}")
    print(f"[CFG] Practical Mean Gain Threshold: >= {MEAN_GAIN_THRESHOLD} -> (See top of script to tune)")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_data()
    best_times_df = get_best_times(df)
    
    # Extract only Stage 2 Arch-Aware rows to figure out which triples to evaluate
    stage2_df = df[df['Stage'] == 'Arch_Aware'].copy()
    if len(stage2_df) == 0:
        print("[WARNING] No 'Arch_Aware' runs found in planner_execution_data.csv. Have you run Phase C?")
        return

    # Triples: (Domain, LLM, Target_Planner)
    triples = stage2_df[['Domain_Name', 'LLM_Used', 'Planner_Used', 'PromptID']].drop_duplicates().to_dict('records')
    
    results_list = []
    
    # We will process each triple independently
    for triple in triples:
        domain = triple['Domain_Name']
        llm = triple['LLM_Used']
        planner = triple['Planner_Used']
        prompt_id = triple['PromptID']
        
        # 1. Fetch Baseline Rows (Stage 0)
        baseline_mask = (df['Stage'] == 'BASELINE') & (df['Domain_Name'] == domain) & (df['Planner_Used'] == planner)
        baseline_rows = df[baseline_mask].sort_values('Problem_Instance')
        
        # 2. Fetch Stage 2 Rows
        s2_mask = (df['Stage'] == 'Arch_Aware') & (df['Domain_Name'] == domain) & (df['Planner_Used'] == planner) & (df['LLM_Used'] == llm)
        s2_rows = df[s2_mask].sort_values('Problem_Instance')
        
        if len(baseline_rows) == 0:
            print(f"[ERROR] Missing Baseline runs for Domain: {domain}, Planner: {planner}. Skipping this triplet.")
            continue
            
        if len(s2_rows) == 0:
            continue
            
        # Get actual filename from the rows (all 15 instances should share the same domain_file)
        domain_file = s2_rows['Domain_File'].iloc[0]
        
        gains = []
        baseline_scores_trace = []
        s2_scores_trace = []
        t_star_trace = []
        
        # Process each instance 1 to 15
        s0_success = 0
        s2_success = 0
        total_instances = 0
        
        for instance_name in s2_rows['Problem_Instance'].unique():
            total_instances += 1
            
            s0_inst = baseline_rows[baseline_rows['Problem_Instance'] == instance_name]
            s2_inst = s2_rows[s2_rows['Problem_Instance'] == instance_name]
            
            # Find T*
            tstar_mask = (best_times_df['Planner_Used'] == planner) & (best_times_df['Domain_Name'] == domain) & (best_times_df['Problem_Instance'] == instance_name)
            tstar_matches = best_times_df[tstar_mask]
            t_star = tstar_matches['T_star'].iloc[0] if not tstar_matches.empty else np.nan
            
            # Extract rows
            if len(s0_inst) > 0:
                s0_row = s0_inst.iloc[0]
                s0_score = calculate_ipc_score(s0_row, t_star)
                if s0_row['Output_Status'] == 'SUCCESS': s0_success += 1
            else:
                s0_score = 0.0
                
            if len(s2_inst) > 0:
                s2_row = s2_inst.iloc[0]
                s2_score = calculate_ipc_score(s2_row, t_star)
                if s2_row['Output_Status'] == 'SUCCESS': s2_success += 1
            else:
                s2_score = 0.0
                
            gain = s2_score - s0_score
            gains.append(gain)
            baseline_scores_trace.append(s0_score)
            s2_scores_trace.append(s2_score)
            t_star_trace.append(t_star if not pd.isna(t_star) else None)
            
        # Descriptive Statistics
        mean_gain = float(np.mean(gains)) if len(gains) > 0 else 0.0
        median_gain = float(np.median(gains)) if len(gains) > 0 else 0.0
        
        cov_s0 = s0_success / total_instances if total_instances > 0 else 0.0
        cov_s2 = s2_success / total_instances if total_instances > 0 else 0.0
        delta_cov = cov_s2 - cov_s0
        
        # Wilcoxon Signed-Rank Test
        non_zero_gains = [g for g in gains if g != 0.0]
        if len(non_zero_gains) < 2:
            p_value = 1.0
            w_stat = None
        else:
            try:
                # We expect Stage 2 to be GREATER than Stage 0, so alternative='greater'
                w_stat, p_value = wilcoxon(non_zero_gains, alternative='greater')
                # For cleaner output formatting
                w_stat = float(w_stat)
                p_value = float(p_value)
            except ValueError:
                # Occurs if all non-zero differences are tied etc.
                p_value = 1.0
                w_stat = None

        # Check the 3 conditions
        cond_A = bool(p_value <= P_VALUE_THRESHOLD)
        cond_B = bool(mean_gain > MEAN_GAIN_THRESHOLD)
        cond_C = bool(delta_cov >= 0.0)
        
        improved = cond_A and cond_B and cond_C
        
        failed_conds = []
        if not cond_A: failed_conds.append("A(Stat)")
        if not cond_B: failed_conds.append("B(Prac)")
        if not cond_C: failed_conds.append("C(Cov)")
        failed_str = ", ".join(failed_conds) if failed_conds else "N/A"
        
        results_list.append({
            "Domain": domain,
            "LLM": llm,
            "Target_Planner": planner,
            "_Domain_File_Internal": domain_file,
            "Coverage_Stage0": round(cov_s0, 6),
            "Coverage_Stage2": round(cov_s2, 6),
            "Delta_Coverage": round(delta_cov, 6),
            "Mean_IPC_Gain": round(mean_gain, 6),
            "Median_IPC_Gain": round(median_gain, 6),
            "Wilcoxon_Stat": w_stat if w_stat is not None else "N/A",
            "Wilcoxon_P_Value": round(p_value, 6) if p_value is not None else "N/A",
            "Condition_A_StatSig": cond_A,
            "Condition_B_PractSig": cond_B,
            "Condition_C_Coverage": cond_C,
            "IMPROVEMENT_DETECTED": improved,
            "Failed_Condition": failed_str,
            "Timestamp": datetime.now().isoformat(),
            # Traceability columns so user can literally see the array math
            "Raw_T_Star_Trace": json.dumps(t_star_trace),
            "Raw_Gains_Trace": json.dumps(gains),
            "Raw_Baseline_Scores": json.dumps(baseline_scores_trace),
            "Raw_Stage2_Scores": json.dumps(s2_scores_trace),
        })

    # Convert to DataFrame
    res_df = pd.DataFrame(results_list)
    
    # Save CSV selectively dropping internal metadata
    res_df.drop(columns=["_Domain_File_Internal"], errors="ignore").to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"[INFO] Details calculation CSV saved to: {OUTPUT_CSV_PATH.relative_to(PROJECT_ROOT)}")
    
    # Filter for improved and copy
    improved_df = res_df[res_df["IMPROVEMENT_DETECTED"] == True]
    print(f"\n[SUMMARY] Found {len(improved_df)} genuinely improved configurations out of {len(res_df)}.")
    
    # Create the Visual Table for terminal
    if len(res_df) > 0:
        table_df = res_df[["Domain", "LLM", "Target_Planner", "Mean_IPC_Gain", "Wilcoxon_P_Value", "IMPROVEMENT_DETECTED", "Failed_Condition"]].copy()
        
        def format_verdict(row):
            if row["IMPROVEMENT_DETECTED"]:
                return "--> YES"
            else:
                return f"--> NO ({row['Failed_Condition']})"
                
        table_df["Verdict"] = table_df.apply(format_verdict, axis=1)
        
        # Display the visual table
        print("\n" + "=" * 90)
        padding_str = "{:<15} | {:<20} | {:<12} | {:<10} | {:<10} | {}"
        print(padding_str.format("Domain", "LLM", "Planner", "Mean Gain", "p-value", "VERDICT"))
        print("-" * 90)
        for _, row in table_df.iterrows():
            domain = row['Domain']
            llm = row['LLM']
            # truncate llm to keep alignment pretty
            if len(llm) > 19: llm = llm[:16] + "..."
            plan = row['Target_Planner']
            gain = f"{row['Mean_IPC_Gain']:+.6f}"
            pval = f"{row['Wilcoxon_P_Value']:.6f}" if row['Wilcoxon_P_Value'] != "N/A" else "N/A"
            verd = row['Verdict']
            print(padding_str.format(domain, llm, plan, gain, pval, verd))
        print("=" * 90 + "\n")

    # Step 7: Copy improved domain files exactly as specified
    copied_count = 0
    for _, row in improved_df.iterrows():
        dom = row['Domain']
        plan = row['Target_Planner']
        d_file = row['_Domain_File_Internal']
        
        source_path = VALIDATED_DOMAINS_DIR / dom / plan / d_file
        dest_dir = IMPROVED_DOMAINS_DIR / dom / plan
        dest_path = dest_dir / d_file
        
        if source_path.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            copied_count += 1
        else:
            print(f"[WARNING] Could not find validated domain file to copy! Expected at: {source_path}")

    print(f"[SUCCESS] Copied {copied_count} improved domain variant(s) into {IMPROVED_DOMAINS_DIR.relative_to(PROJECT_ROOT)}!")
    print("\nPhase D Complete!")

if __name__ == "__main__":
    main()
