"""
================================================================================
IPC SCORE COMPUTATION — GLOBAL CROSS-STAGE ANALYSIS
================================================================================
This script computes IPC scores using TWO reference contexts:
  1. Configuration Sensitivity (per-planner): T* = best time for THIS planner
  2. Simulated Competition (all planners): T* = best time for ANY planner

It reads ALL data from planner_execution_data.csv (which contains BASELINE,
General, Arch_Aware, Cross_Test, Feedback_Loop1/2/3 stages) and produces:

  - A methodology report (markdown)
  - T* reference tables for both contexts
  - Stage 0 IPC tables (4 planners x 5 domains)
  - Stage 1 IPC tables (one per LLM, 4 planners x 5 domains)
  - Stage 2 IPC tables (one per LLM, 4 planners x 20 (domain,prompt-planner) pairs)
  - Stage 3 IPC table (218 iterations: Domain, LLM, Planner, Iter#, Global Score)
  
Author: Generated for bachelor thesis analysis
Date: 2026-06-05
================================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

# ===== PATHS =====
BASE_DIR = Path(r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator")
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "1_Global_IPC_Score"

MAIN_CSV = RESULTS_DIR / "planner_execution_data.csv"
ITERATION_CSV = RESULTS_DIR / "feedback_loop" / "iteration_tracking.csv"

# ===== CONSTANTS =====
PLANNERS = ["bfws", "lama", "decstar", "madagascar"]
DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
INSTANCES = [
    "instance-01.pddl", "instance-02.pddl", "instance-03.pddl", "instance-04.pddl",
    "instance-07.pddl", "instance-08.pddl", "instance-09.pddl", "instance-11.pddl",
    "instance-12.pddl", "instance-13.pddl", "instance-14.pddl", "instance-16.pddl",
    "instance-17.pddl", "instance-18.pddl", "instance-19.pddl"
]

# PromptID mapping: which PromptID integer part = which planner was the PROMPT TARGET
PROMPTID_TO_PLANNER = {1: "lama", 2: "decstar", 3: "bfws", 4: "madagascar"}
PLANNER_TO_PROMPTID = {v: k for k, v in PROMPTID_TO_PLANNER.items()}

# LLM display names
LLM_DISPLAY = {
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "claude-opus-4-6": "Claude Opus 4.6",
    "deepseek-reasoner": "DeepSeek-R1",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1 Pro"
}

LLM_ORDER = ["gpt-5.4-2026-03-05", "claude-opus-4-6", "deepseek-reasoner", "gemini-3.1-pro-preview-customtools"]

# ===== LOAD DATA =====
print("Loading data...")
df = pd.read_csv(MAIN_CSV)
iteration_tracking = pd.read_csv(ITERATION_CSV)

# Normalize Runtime_wall_s: ensure it's numeric, replace N/A with NaN
df["Runtime_wall_s"] = pd.to_numeric(df["Runtime_wall_s"], errors="coerce")

# For TIMEOUT and FAILURE: runtime is NOT usable for IPC score, mark as unsolved
# Only SUCCESS runs have meaningful runtimes
df["solved"] = df["Output_Status"] == "SUCCESS"

print("Total rows:", len(df))
print("Stages:", df["Stage"].value_counts().to_dict())


# ===== IPC SCORE FORMULA =====
def compute_ipc_score(runtime, t_star):
    """
    IPC Agile Track Score for a single instance:
    
    Score(p) = 1 / (1 + log10(T(p) / T*(p)))
    
    Where:
      T(p)  = runtime of the configuration being evaluated on instance p
      T*(p) = best known runtime for instance p (the reference)
    
    If T(p) is unsolved (TIMEOUT/FAILURE): Score(p) = 0
    If T*(p) is unsolved (no config solved it): Score(p) = 0 for all
    If T(p) == T*(p): Score(p) = 1 (maximum)
    
    The score is always in [0, 1].
    """
    if pd.isna(runtime) or pd.isna(t_star) or t_star <= 0:
        return 0.0
    if runtime <= 0:
        # Edge case: treat as essentially instant, give max score
        runtime = 0.001
    ratio = runtime / t_star
    if ratio <= 0:
        return 0.0
    score = 1.0 / (1.0 + np.log10(ratio))
    return max(0.0, score)


# ===== HELPER: Get runtime for a (domain, instance, planner) in a given set of rows =====
def get_runtime(subset_df, domain, instance, planner):
    """Get the runtime for a specific (domain, instance, planner) from a dataframe subset.
    Returns the runtime if solved, NaN if not solved or not found."""
    mask = (
        (subset_df["Domain_Name"] == domain) &
        (subset_df["Problem_Instance"] == instance) &
        (subset_df["Planner_Used"] == planner) &
        (subset_df["solved"])
    )
    rows = subset_df[mask]
    if len(rows) == 0:
        return np.nan
    # If multiple rows match, take the minimum runtime (best run)
    return rows["Runtime_wall_s"].min()


# ==========================================================================
# STEP 1: COMPUTE T* REFERENCE TIMES
# ==========================================================================
print("\n===== Computing T* reference times =====")

# --- Separate data by stage ---
s0 = df[df["Stage"] == "BASELINE"]
s1 = df[df["Stage"] == "General"]
s2_target = df[df["Stage"] == "Arch_Aware"]  # Only target-planner runs
s2_cross = df[df["Stage"] == "Cross_Test"]   # Cross-test runs
s3_fb1 = df[df["Stage"] == "Feedback_Loop1"]
s3_fb2 = df[df["Stage"] == "Feedback_Loop2"]
s3_fb3 = df[df["Stage"] == "Feedback_Loop3"]

# All feedback loop data combined
s3_all = pd.concat([s3_fb1, s3_fb2, s3_fb3])

# All data combined (for simulated competition T*)
all_data = df.copy()

# --- T* Configuration Sensitivity: best time per (planner, domain, instance) ---
# across ALL stages and ALL LLMs/configs, but ONLY for that planner
print("Computing T* Configuration Sensitivity...")
t_star_config = {}  # (planner, domain, instance) -> best_runtime

for planner in PLANNERS:
    planner_data = all_data[
        (all_data["Planner_Used"] == planner) &
        (all_data["solved"])
    ]
    for domain in DOMAINS:
        for instance in INSTANCES:
            mask = (
                (planner_data["Domain_Name"] == domain) &
                (planner_data["Problem_Instance"] == instance)
            )
            runtimes = planner_data[mask]["Runtime_wall_s"]
            if len(runtimes) > 0:
                t_star_config[(planner, domain, instance)] = runtimes.min()
            else:
                t_star_config[(planner, domain, instance)] = np.nan

# --- T* Simulated Competition: best time per (domain, instance) ---
# across ALL planners, ALL stages, ALL LLMs
print("Computing T* Simulated Competition...")
t_star_comp = {}  # (domain, instance) -> best_runtime

solved_data = all_data[all_data["solved"]]
for domain in DOMAINS:
    for instance in INSTANCES:
        mask = (
            (solved_data["Domain_Name"] == domain) &
            (solved_data["Problem_Instance"] == instance)
        )
        runtimes = solved_data[mask]["Runtime_wall_s"]
        if len(runtimes) > 0:
            t_star_comp[(domain, instance)] = runtimes.min()
        else:
            t_star_comp[(domain, instance)] = np.nan


# ==========================================================================
# STEP 2: COMPUTE IPC SCORES FOR EACH STAGE
# ==========================================================================

def compute_stage_score_per_planner_domain(stage_df, context="config"):
    """
    Compute total IPC score per (planner, domain) from a stage dataframe.
    
    context = "config" -> use T* per (planner, domain, instance)
    context = "comp"   -> use T* per (domain, instance) only
    
    Returns dict: (planner, domain) -> total_score (sum over instances)
    """
    results = {}
    for planner in PLANNERS:
        for domain in DOMAINS:
            total_score = 0.0
            for instance in INSTANCES:
                # Get this config's runtime
                runtime = get_runtime(stage_df, domain, instance, planner)
                
                # Get reference time
                if context == "config":
                    t_star = t_star_config.get((planner, domain, instance), np.nan)
                else:
                    t_star = t_star_comp.get((domain, instance), np.nan)
                
                if pd.isna(runtime):
                    score = 0.0
                elif pd.isna(t_star):
                    score = 0.0
                else:
                    score = compute_ipc_score(runtime, t_star)
                
                total_score += score
            results[(planner, domain)] = round(total_score, 4)
    return results


def compute_s1_scores_by_llm(context="config"):
    """Stage 1: one set of scores per LLM. Each LLM has one domain file per domain.
    Returns: {llm: {(planner, domain): score}}"""
    results = {}
    for llm in LLM_ORDER:
        llm_data = s1[(s1["LLM_Used"] == llm)]
        llm_scores = {}
        for planner in PLANNERS:
            for domain in DOMAINS:
                total_score = 0.0
                for instance in INSTANCES:
                    runtime = get_runtime(llm_data, domain, instance, planner)
                    if context == "config":
                        t_star = t_star_config.get((planner, domain, instance), np.nan)
                    else:
                        t_star = t_star_comp.get((domain, instance), np.nan)
                    
                    if pd.isna(runtime) or pd.isna(t_star):
                        score = 0.0
                    else:
                        score = compute_ipc_score(runtime, t_star)
                    total_score += score
                llm_scores[(planner, domain)] = round(total_score, 4)
        results[llm] = llm_scores
    return results


def compute_s2_scores_by_llm(context="config"):
    """Stage 2: For each LLM, compute scores for 4 planners x 20 (domain, prompt-planner) pairs.
    
    In Arch_Aware: PromptID = target planner (1=lama, 2=decstar, 3=bfws, 4=madagascar)
    The Planner_Used column is the planner that actually ran (always == target in Arch_Aware).
    
    BUT the user also wants to see the Cross_Test data:
    For each LLM, for each domain, there are 4 domain files (one per target planner prompt).
    Each domain file was tested on ONLY the target planner in Arch_Aware, 
    and on the 3 OTHER planners in Cross_Test.
    
    So the 20 columns are: (domain, prompt_target_planner) = 5 domains x 4 prompt targets = 20
    The 4 rows are the 4 planners that ACTUALLY RAN (the evaluating planner).
    
    For a given (LLM, domain, prompt_target, evaluating_planner):
      - If prompt_target == evaluating_planner: look in Arch_Aware
      - If prompt_target != evaluating_planner: look in Cross_Test
      - If not found in either: N/A
    
    Returns: {llm: {(evaluating_planner, domain, prompt_target_planner): score_or_None}}
    """
    results = {}
    
    for llm in LLM_ORDER:
        llm_aa = s2_target[s2_target["LLM_Used"] == llm]
        llm_ct = s2_cross[s2_cross["LLM_Used"] == llm]
        
        llm_scores = {}
        for eval_planner in PLANNERS:
            for domain in DOMAINS:
                for prompt_target in PLANNERS:
                    prompt_id_base = PLANNER_TO_PROMPTID[prompt_target]
                    
                    if eval_planner == prompt_target:
                        # Look in Arch_Aware
                        source = llm_aa[
                            (llm_aa["PromptID"] == prompt_id_base) &
                            (llm_aa["Domain_Name"] == domain) &
                            (llm_aa["Planner_Used"] == eval_planner)
                        ]
                    else:
                        # Look in Cross_Test
                        source = llm_ct[
                            (llm_ct["PromptID"] == prompt_id_base) &
                            (llm_ct["Domain_Name"] == domain) &
                            (llm_ct["Planner_Used"] == eval_planner)
                        ]
                    
                    if len(source) == 0:
                        # No data at all for this combo
                        llm_scores[(eval_planner, domain, prompt_target)] = None
                        continue
                    
                    # Compute IPC score summed over instances
                    total_score = 0.0
                    for instance in INSTANCES:
                        mask = (
                            (source["Problem_Instance"] == instance) &
                            (source["solved"])
                        )
                        runtimes = source[mask]["Runtime_wall_s"]
                        
                        if len(runtimes) > 0:
                            runtime = runtimes.min()
                        else:
                            runtime = np.nan
                        
                        if context == "config":
                            t_star = t_star_config.get((eval_planner, domain, instance), np.nan)
                        else:
                            t_star = t_star_comp.get((domain, instance), np.nan)
                        
                        if pd.isna(runtime) or pd.isna(t_star):
                            score = 0.0
                        else:
                            score = compute_ipc_score(runtime, t_star)
                        total_score += score
                    
                    llm_scores[(eval_planner, domain, prompt_target)] = round(total_score, 4)
        
        results[llm] = llm_scores
    return results


def compute_s3_iteration_scores(context="config"):
    """Stage 3: For each of the 218 iterations in iteration_tracking.csv,
    compute the global IPC score.
    
    Each iteration corresponds to a specific (domain, llm, target_planner, iteration#).
    The planner execution data is in Feedback_Loop1/2/3 stages, matched by:
      - Stage = Feedback_LoopN (where N = iteration number)
      - Domain_Name = domain
      - LLM_Used = llm
      - Planner_Used = target_planner
      - PromptID = PLANNER_TO_PROMPTID[target_planner].iteration  (e.g., 1.1, 1.2, 1.3 for lama)
    
    Returns: list of dicts with Domain, LLM, Planner, Iteration, Score, Validation_Status
    """
    results = []
    
    for _, row in iteration_tracking.iterrows():
        domain = row["Domain"]
        llm_raw = row["LLM"]
        target_planner = row["Target_Planner"]
        iteration = int(row["Iteration"])
        validation = row["Validation_Status"]
        
        # Map LLM names from iteration_tracking to the names in planner_execution_data
        llm_map = {
            "gpt-5.4-2026-03-05": "gpt-5.4-2026-03-05",
            "claude-opus-4-6": "claude-opus-4-6",
            "deepseek-reasoner": "deepseek-reasoner",
            "gemini-3.1-pro-preview-customtools": "gemini-3.1-pro-preview-customtools",
        }
        llm = llm_map.get(llm_raw, llm_raw)
        
        # If not VALID, score is 0 or N/A — but we still want to show the row
        if validation != "VALID":
            results.append({
                "Domain": domain,
                "LLM": LLM_DISPLAY.get(llm, llm),
                "Planner": target_planner,
                "Iteration": iteration,
                "Score": "N/A (Invalid: {})".format(validation),
                "Score_Numeric": np.nan,
            })
            continue
        
        # Find the corresponding planner execution data
        stage_name = "Feedback_Loop{}".format(iteration)
        prompt_id = PLANNER_TO_PROMPTID[target_planner] + iteration * 0.1
        # PromptID pattern: base.iteration -> e.g., lama=1, iter1=1.1, iter2=1.2, iter3=1.3
        
        stage_data = df[
            (df["Stage"] == stage_name) &
            (df["Domain_Name"] == domain) &
            (df["LLM_Used"] == llm) &
            (df["Planner_Used"] == target_planner)
        ]
        
        if len(stage_data) == 0:
            results.append({
                "Domain": domain,
                "LLM": LLM_DISPLAY.get(llm, llm),
                "Planner": target_planner,
                "Iteration": iteration,
                "Score": "N/A (No exec data)",
                "Score_Numeric": np.nan,
            })
            continue
        
        # Compute IPC score summed over instances
        total_score = 0.0
        for instance in INSTANCES:
            mask = (
                (stage_data["Problem_Instance"] == instance) &
                (stage_data["solved"])
            )
            runtimes = stage_data[mask]["Runtime_wall_s"]
            
            if len(runtimes) > 0:
                runtime = runtimes.min()
            else:
                runtime = np.nan
            
            if context == "config":
                t_star = t_star_config.get((target_planner, domain, instance), np.nan)
            else:
                t_star = t_star_comp.get((domain, instance), np.nan)
            
            if pd.isna(runtime) or pd.isna(t_star):
                score = 0.0
            else:
                score = compute_ipc_score(runtime, t_star)
            total_score += score
        
        results.append({
            "Domain": domain,
            "LLM": LLM_DISPLAY.get(llm, llm),
            "Planner": target_planner,
            "Iteration": iteration,
            "Score": round(total_score, 4),
            "Score_Numeric": round(total_score, 4),
        })
    
    return results


# ==========================================================================
# STEP 3: RUN ALL COMPUTATIONS
# ==========================================================================

for context_name, context_key in [("Configuration_Sensitivity", "config"), ("Simulated_Competition", "comp")]:
    print("\n" + "=" * 70)
    print("COMPUTING: {}".format(context_name))
    print("=" * 70)
    
    output_subdir = OUTPUT_DIR / "tables" / context_name
    os.makedirs(output_subdir, exist_ok=True)
    
    # --- Stage 0 ---
    print("  Stage 0...")
    s0_scores = compute_stage_score_per_planner_domain(s0, context=context_key)
    
    # Build table: rows=planners, cols=domains
    s0_table = pd.DataFrame(index=PLANNERS, columns=DOMAINS, dtype=float)
    for planner in PLANNERS:
        for domain in DOMAINS:
            s0_table.loc[planner, domain] = s0_scores[(planner, domain)]
    
    # Add row totals and column totals
    s0_table["TOTAL"] = s0_table.sum(axis=1).round(4)
    s0_table.loc["TOTAL"] = s0_table.sum(axis=0).round(4)
    
    s0_table.to_csv(output_subdir / "S0_Baseline_IPC.csv")
    print("    Saved S0 table. Grand total =", s0_table.loc["TOTAL", "TOTAL"])
    
    # --- Stage 1 ---
    print("  Stage 1...")
    s1_scores = compute_s1_scores_by_llm(context=context_key)
    
    for llm in LLM_ORDER:
        llm_name = LLM_DISPLAY[llm]
        table = pd.DataFrame(index=PLANNERS, columns=DOMAINS, dtype=float)
        for planner in PLANNERS:
            for domain in DOMAINS:
                table.loc[planner, domain] = s1_scores[llm][(planner, domain)]
        table["TOTAL"] = table.sum(axis=1).round(4)
        table.loc["TOTAL"] = table.sum(axis=0).round(4)
        
        filename = "S1_General_{}.csv".format(llm_name.replace(" ", "_").replace(".", "_"))
        table.to_csv(output_subdir / filename)
        print("    Saved {} - Grand total = {}".format(llm_name, table.loc["TOTAL", "TOTAL"]))
    
    # --- Stage 2 ---
    print("  Stage 2...")
    s2_scores = compute_s2_scores_by_llm(context=context_key)
    
    for llm in LLM_ORDER:
        llm_name = LLM_DISPLAY[llm]
        # Columns: (domain, prompt_target_planner) = 20 columns
        col_tuples = []
        for domain in DOMAINS:
            for pt in PLANNERS:
                col_tuples.append("{}_for_{}".format(domain, pt))
        
        table = pd.DataFrame(index=PLANNERS, columns=col_tuples)
        for eval_planner in PLANNERS:
            for domain in DOMAINS:
                for prompt_target in PLANNERS:
                    col = "{}_for_{}".format(domain, prompt_target)
                    val = s2_scores[llm].get((eval_planner, domain, prompt_target), None)
                    if val is None:
                        table.loc[eval_planner, col] = "N/A"
                    else:
                        table.loc[eval_planner, col] = val
        
        filename = "S2_ArchAware_{}.csv".format(llm_name.replace(" ", "_").replace(".", "_"))
        table.to_csv(output_subdir / filename)
        print("    Saved", llm_name)
    
    # --- Stage 3 ---
    print("  Stage 3...")
    s3_scores = compute_s3_iteration_scores(context=context_key)
    
    s3_df = pd.DataFrame(s3_scores)
    s3_df = s3_df[["Domain", "LLM", "Planner", "Iteration", "Score"]]
    
    filename = "S3_FeedbackLoop_All_Iterations.csv"
    s3_df.to_csv(output_subdir / filename, index=False)
    print("    Saved S3 table ({} rows)".format(len(s3_df)))
    
    # --- T* Reference Table ---
    print("  T* reference table...")
    if context_key == "config":
        t_star_records = []
        for planner in PLANNERS:
            for domain in DOMAINS:
                for instance in INSTANCES:
                    val = t_star_config.get((planner, domain, instance), np.nan)
                    # Find which stage provided the best time
                    best_stage = "N/A"
                    if not pd.isna(val):
                        for stage_name, stage_df_check in [
                            ("BASELINE", s0), ("General", s1), ("Arch_Aware", s2_target),
                            ("Cross_Test", s2_cross),
                            ("Feedback_Loop1", s3_fb1), ("Feedback_Loop2", s3_fb2), ("Feedback_Loop3", s3_fb3)
                        ]:
                            check = stage_df_check[
                                (stage_df_check["Domain_Name"] == domain) &
                                (stage_df_check["Problem_Instance"] == instance) &
                                (stage_df_check["Planner_Used"] == planner) &
                                (stage_df_check["solved"])
                            ]
                            if len(check) > 0 and abs(check["Runtime_wall_s"].min() - val) < 0.0001:
                                best_stage = stage_name
                                # Also get the LLM if applicable
                                best_row = check.loc[check["Runtime_wall_s"].idxmin()]
                                llm_used = best_row.get("LLM_Used", "N/A")
                                if llm_used != "N/A" and not pd.isna(llm_used):
                                    best_stage += " ({})".format(LLM_DISPLAY.get(llm_used, llm_used))
                                break
                    
                    t_star_records.append({
                        "Planner": planner,
                        "Domain": domain,
                        "Instance": instance,
                        "T_star": round(val, 6) if not pd.isna(val) else "UNSOLVED",
                        "Source_Stage": best_stage
                    })
        t_star_df = pd.DataFrame(t_star_records)
        t_star_df.to_csv(output_subdir / "T_star_reference.csv", index=False)
        print("    Saved T* reference ({} entries, {} unsolved)".format(
            len(t_star_df), len(t_star_df[t_star_df["T_star"] == "UNSOLVED"])))
    else:
        t_star_records = []
        for domain in DOMAINS:
            for instance in INSTANCES:
                val = t_star_comp.get((domain, instance), np.nan)
                best_stage = "N/A"
                best_planner = "N/A"
                if not pd.isna(val):
                    for stage_name, stage_df_check in [
                        ("BASELINE", s0), ("General", s1), ("Arch_Aware", s2_target),
                        ("Cross_Test", s2_cross),
                        ("Feedback_Loop1", s3_fb1), ("Feedback_Loop2", s3_fb2), ("Feedback_Loop3", s3_fb3)
                    ]:
                        check = stage_df_check[
                            (stage_df_check["Domain_Name"] == domain) &
                            (stage_df_check["Problem_Instance"] == instance) &
                            (stage_df_check["solved"])
                        ]
                        if len(check) > 0 and abs(check["Runtime_wall_s"].min() - val) < 0.0001:
                            best_row = check.loc[check["Runtime_wall_s"].idxmin()]
                            best_stage = stage_name
                            best_planner = best_row["Planner_Used"]
                            llm_used = best_row.get("LLM_Used", "N/A")
                            if llm_used != "N/A" and not pd.isna(llm_used):
                                best_stage += " ({})".format(LLM_DISPLAY.get(llm_used, llm_used))
                            break
                
                t_star_records.append({
                    "Domain": domain,
                    "Instance": instance,
                    "T_star": round(val, 6) if not pd.isna(val) else "UNSOLVED",
                    "Best_Planner": best_planner,
                    "Source_Stage": best_stage
                })
        t_star_df = pd.DataFrame(t_star_records)
        t_star_df.to_csv(output_subdir / "T_star_reference.csv", index=False)
        print("    Saved T* reference ({} entries, {} unsolved)".format(
            len(t_star_df), len(t_star_df[t_star_df["T_star"] == "UNSOLVED"])))


# ==========================================================================
# STEP 4: GENERATE METHODOLOGY REPORT
# ==========================================================================
print("\n===== Generating methodology report =====")

# Collect key stats for the report
s0_config = pd.read_csv(OUTPUT_DIR / "tables" / "Configuration_Sensitivity" / "S0_Baseline_IPC.csv", index_col=0)
s0_comp = pd.read_csv(OUTPUT_DIR / "tables" / "Simulated_Competition" / "S0_Baseline_IPC.csv", index_col=0)

# Count unsolved instances
config_tstar = pd.read_csv(OUTPUT_DIR / "tables" / "Configuration_Sensitivity" / "T_star_reference.csv")
comp_tstar = pd.read_csv(OUTPUT_DIR / "tables" / "Simulated_Competition" / "T_star_reference.csv")

config_unsolved = len(config_tstar[config_tstar["T_star"] == "UNSOLVED"])
comp_unsolved = len(comp_tstar[comp_tstar["T_star"] == "UNSOLVED"])
total_config = len(PLANNERS) * len(DOMAINS) * len(INSTANCES)
total_comp = len(DOMAINS) * len(INSTANCES)

# Build the T* summary tables for the report
config_solved_counts = {}
for planner in PLANNERS:
    for domain in DOMAINS:
        count = len(config_tstar[
            (config_tstar["Planner"] == planner) &
            (config_tstar["Domain"] == domain) &
            (config_tstar["T_star"] != "UNSOLVED")
        ])
        config_solved_counts[(planner, domain)] = count

comp_solved_counts = {}
for domain in DOMAINS:
    count = len(comp_tstar[
        (comp_tstar["Domain"] == domain) &
        (comp_tstar["T_star"] != "UNSOLVED")
    ])
    comp_solved_counts[domain] = count


# Build report using list-based string building to avoid .format() issues
lines = []
lines.append("# IPC Score Methodology & Global T* Reference Report")
lines.append("")
lines.append("> **Project:** Architecture-Aware Domain Model Configuration  ")
lines.append("> **Date Generated:** 2026-06-05  ")
lines.append("> **Data Source:** `results/planner_execution_data.csv` (7,350 rows across 7 stages)")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. The IPC Score Formula")
lines.append("")
lines.append("We use the **IPC Agile Track Score** formula as defined by the International Planning Competition (IPC). This is the same formula used in IPC competitions for evaluating planner speed.")
lines.append("")
lines.append("### Formula")
lines.append("")
lines.append("For a single problem instance p:")
lines.append("")
lines.append("```")
lines.append("Score(p) = 1 / (1 + log10( T(p) / T*(p) ))")
lines.append("```")
lines.append("")
lines.append("Where:")
lines.append("- **T(p)** = wall-clock runtime of the configuration being evaluated on instance p")
lines.append("- **T\\*(p)** = the **best known runtime** for instance p (the reference time)")
lines.append("")
lines.append("### Scoring Rules")
lines.append("")
lines.append("| Condition | Score |")
lines.append("|-----------|-------|")
lines.append("| Configuration **solved** the instance | `1 / (1 + log10(T(p)/T*(p)))` in (0, 1] |")
lines.append("| T(p) = T\\*(p) (configuration IS the best) | **1.0** (maximum) |")
lines.append("| T(p) = 10 x T\\*(p) (10x slower than best) | **0.5** |")
lines.append("| Configuration **did NOT solve** (TIMEOUT/FAILURE) | **0.0** |")
lines.append("| **No configuration** solved this instance (T\\* undefined) | **0.0** for all |")
lines.append("")
lines.append("### Aggregation")
lines.append("")
lines.append("The **total IPC score** for a configuration across n instances is the **sum** of individual scores:")
lines.append("")
lines.append("```")
lines.append("Total_IPC_Score = SUM of Score(p) for all p in (instance-01, ..., instance-19)")
lines.append("```")
lines.append("")
lines.append("Maximum possible score per domain = **15.0** (one point per instance, 15 instances per domain).  ")
lines.append("Maximum possible score across all domains = **75.0** (15 x 5 domains).")
lines.append("")
lines.append("### Is This the Same as IPC Competitions?")
lines.append("")
lines.append("**Yes, with one clarification.** The formula `1/(1+log10(T/T*))` is the standard IPC Agile Track scoring function. In official IPC competitions:")
lines.append("- T\\* is determined by the best competitor across all submitted planners")
lines.append("- The timeout is typically 1800s (30 min) or 300s (5 min for Agile Track)")
lines.append("")
lines.append("In our thesis:")
lines.append("- Our timeout is **360 seconds** (6 minutes), as defined in our experimental setup")
lines.append("- T\\* is computed from our own experimental data (see Section 2)")
lines.append("- The formula itself is **identical** to the official IPC definition")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 2. Two T* Contexts: Configuration Sensitivity vs. Simulated Competition")
lines.append("")
lines.append("We compute IPC scores under **two different definitions of T\\***, each answering a different question:")
lines.append("")
lines.append("### 2.1 Configuration Sensitivity (Per-Planner)")
lines.append("")
lines.append('> **Question:** "How well does this configuration perform compared to the best this SAME planner has ever achieved?"')
lines.append("")
lines.append("```")
lines.append("T*_config(planner, domain, instance) = min( T(p) across ALL stages, ALL LLMs, ALL configs )")
lines.append("                                        WHERE Planner_Used = planner")
lines.append("```")
lines.append("")
lines.append("- T\\* is specific to **each planner**")
lines.append("- A planner is only compared against **itself** across different domain configurations")
lines.append("- This isolates the effect of domain configuration on a specific planner")
lines.append("- **" + str(config_unsolved) + " out of " + str(total_config) + " (planner x domain x instance) combinations have T\\* = UNSOLVED**")
lines.append("")
lines.append("#### Solved Instance Counts (Configuration Sensitivity)")
lines.append("")
lines.append("| Planner | " + " | ".join(DOMAINS) + " | Total |")
lines.append("|---------|" + "|".join(["-------"] * len(DOMAINS)) + "|-------|")

for planner in PLANNERS:
    vals = [str(config_solved_counts[(planner, d)]) + "/15" for d in DOMAINS]
    total = sum(config_solved_counts[(planner, d)] for d in DOMAINS)
    lines.append("| " + planner + " | " + " | ".join(vals) + " | " + str(total) + "/75 |")

total_per_domain = [sum(config_solved_counts[(p, d)] for p in PLANNERS) for d in DOMAINS]
grand_total = sum(total_per_domain)
lines.append("| **TOTAL** | " + " | ".join([str(t) + "/60" for t in total_per_domain]) + " | **" + str(grand_total) + "/300** |")
lines.append("")
lines.append("### 2.2 Simulated Competition (All Planners)")
lines.append("")
lines.append('> **Question:** "How well does this configuration perform compared to the absolute best ANY planner has ever achieved?"')
lines.append("")
lines.append("```")
lines.append("T*_comp(domain, instance) = min( T(p) across ALL planners, ALL stages, ALL LLMs, ALL configs )")
lines.append("```")
lines.append("")
lines.append("- T\\* is **shared across all planners** — every planner competes against the global best")
lines.append("- A slow planner on an easy instance (where another planner is very fast) will score low even if it solved it")
lines.append("- This simulates a real planning competition scenario")
lines.append("- **" + str(comp_unsolved) + " out of " + str(total_comp) + " (domain x instance) combinations have T\\* = UNSOLVED**")
lines.append("")
lines.append("#### Solved Instance Counts (Simulated Competition)")
lines.append("")
lines.append("| Domain | Solved/15 |")
lines.append("|--------|-----------|")

for domain in DOMAINS:
    lines.append("| " + domain + " | " + str(comp_solved_counts[domain]) + "/15 |")

lines.append("| **TOTAL** | **" + str(sum(comp_solved_counts.values())) + "/75** |")
lines.append("")
lines.append("### 2.3 Key Differences Summary")
lines.append("")
lines.append("| Aspect | Configuration Sensitivity | Simulated Competition |")
lines.append("|--------|--------------------------|----------------------|")
lines.append("| T\\* scope | Per-planner (same planner only) | Global (all planners) |")
lines.append("| T\\* granularity | (planner, domain, instance) | (domain, instance) |")
lines.append("| Total T\\* entries | " + str(total_config) + " | " + str(total_comp) + " |")
lines.append("| Unsolved T\\* entries | " + str(config_unsolved) + " | " + str(comp_unsolved) + " |")
lines.append("| What it measures | Effect of domain config on a specific planner | Absolute competitive position |")
lines.append("| Fair comparison? | Yes — planners compared to themselves | Cross-planner comparison (favors fast planners) |")
lines.append('| Use case | "Did arch-aware prompting help LAMA?" | "Which stage produces the overall best configs?" |')
lines.append("")
lines.append("### 2.4 How T\\* Was Computed")
lines.append("")
lines.append("For **both** contexts, T\\* was computed by scanning **ALL 7,350 rows** in `planner_execution_data.csv`, which includes:")
lines.append("")
lines.append("| Stage | Description | Rows |")
lines.append("|-------|-------------|------|")
lines.append("| BASELINE (S0) | Original domains, 4 planners x 5 domains x 15 instances | 300 |")
lines.append("| General (S1) | General prompt, 4 LLMs x 4 planners x 5 domains x 15 instances | 1,080 |")
lines.append("| Arch_Aware (S2-target) | Arch-aware prompt, target planner only | 1,125 |")
lines.append("| Cross_Test (S2-cross) | Arch-aware domains tested on non-target planners | 1,890 |")
lines.append("| Feedback_Loop1 (S3-iter1) | Feedback loop iteration 1 | 1,125 |")
lines.append("| Feedback_Loop2 (S3-iter2) | Feedback loop iteration 2 | 945 |")
lines.append("| Feedback_Loop3 (S3-iter3) | Feedback loop iteration 3 | 885 |")
lines.append("| **TOTAL** | | **7,350** |")
lines.append("")
lines.append("> [!IMPORTANT]")
lines.append("> T\\* includes data from ALL stages. This means if a Feedback Loop iteration produced the fastest time for an instance, that becomes T\\*. This is the correct approach because T\\* should represent the absolute best achievable time, giving a fair scoring baseline.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 3. Detailed T\\* Reference Values")
lines.append("")
lines.append("The complete T\\* reference tables are saved as CSV files:")
lines.append("- `T_star_reference.csv` in each context's output folder")
lines.append("- Each entry shows the T\\* value, which stage produced it, and which LLM (if applicable)")
lines.append("")
lines.append("The CSV files contain every (planner, domain, instance) triple for Configuration Sensitivity and every (domain, instance) pair for Simulated Competition.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 4. Output Files Generated")
lines.append("")
lines.append("### Configuration Sensitivity")
lines.append("")
lines.append("| File | Description |")
lines.append("|------|-------------|")
lines.append("| `S0_Baseline_IPC.csv` | Stage 0: 4 planners x 5 domains IPC scores |")
lines.append("| `S1_General_<LLM>.csv` (x4) | Stage 1: 4 planners x 5 domains, one table per LLM |")
lines.append("| `S2_ArchAware_<LLM>.csv` (x4) | Stage 2: 4 planners x 20 (domain, prompt-target) columns, one per LLM |")
lines.append("| `S3_FeedbackLoop_All_Iterations.csv` | Stage 3: All 218 iterations with IPC scores |")
lines.append("| `T_star_reference.csv` | All T\\* values with source stage annotations |")
lines.append("")
lines.append("### Simulated Competition")
lines.append("")
lines.append("Same file structure, in the `Simulated_Competition/` subfolder.")
lines.append("")

report = "\n".join(lines)

# Write report
report_path = OUTPUT_DIR / "IPC_Score_Methodology_Report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report)
print("Methodology report saved to:", report_path)

print("\n===== ALL DONE =====")
print("Output directory:", OUTPUT_DIR)
