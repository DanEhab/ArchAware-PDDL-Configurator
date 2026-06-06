"""
================================================================================
SECTION 1: GLOBAL IPC SCORE COMPUTATION — CROSS-STAGE ANALYSIS
================================================================================
Implements all tables (G-T1 through G-T7+) and graphs (G-G1 through G-G6+)
from Phase 5 Analysis Plan Part 2, Section 1.

Reads pre-calculated global IPC scores from:
  analysis/output/cross_stage/1_Global_IPC_Score (Most Important)/tables/

Outputs all results to:
  analysis/output/cross_stage/1_Global_IPC_Score (Most Important)/section1_analysis/

Author: Generated for bachelor thesis analysis
Date: 2026-06-06
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ===== PATHS =====
BASE_DIR = Path(r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator")
RESULTS_DIR = BASE_DIR / "results"
PRECALC_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "1_Global_IPC_Score (Most Important)" / "tables"
OUTPUT_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "1_Global_IPC_Score (Most Important)" / "section1_analysis"
MAIN_CSV = RESULTS_DIR / "planner_execution_data.csv"

# Create output directories
(OUTPUT_DIR / "tables").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "graphs").mkdir(parents=True, exist_ok=True)

# ===== CONSTANTS =====
PLANNERS = ["bfws", "lama", "decstar", "madagascar"]
PLANNER_DISPLAY = {"bfws": "BFWS", "lama": "LAMA", "decstar": "DecStar", "madagascar": "Madagascar"}
DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
INSTANCES = [
    "instance-01.pddl", "instance-02.pddl", "instance-03.pddl", "instance-04.pddl",
    "instance-07.pddl", "instance-08.pddl", "instance-09.pddl", "instance-11.pddl",
    "instance-12.pddl", "instance-13.pddl", "instance-14.pddl", "instance-16.pddl",
    "instance-17.pddl", "instance-18.pddl", "instance-19.pddl"
]
LLM_NAMES = ["GPT-5.4", "Claude Opus 4.6", "DeepSeek-R1", "Gemini 3.1 Pro"]
LLM_FILE_MAP = {
    "GPT-5.4": "GPT-5_4",
    "Claude Opus 4.6": "Claude_Opus_4_6",
    "DeepSeek-R1": "DeepSeek-R1",
    "Gemini 3.1 Pro": "Gemini_3_1_Pro"
}
LLM_RAW_MAP = {
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "claude-opus-4-6": "Claude Opus 4.6",
    "deepseek-reasoner": "DeepSeek-R1",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1 Pro"
}
PROMPTID_TO_PLANNER = {1: "lama", 2: "decstar", 3: "bfws", 4: "madagascar"}
PLANNER_TO_PROMPTID = {v: k for k, v in PROMPTID_TO_PLANNER.items()}

# ===== STYLE =====
STAGE_COLORS = {"S0": "#6c757d", "S1": "#2196F3", "S2": "#FF9800", "S3": "#4CAF50"}
PLANNER_COLORS = {"bfws": "#E53935", "lama": "#1E88E5", "decstar": "#FDD835", "madagascar": "#43A047"}
DOMAIN_COLORS = {
    "barman": "#E53935", "depots": "#1E88E5", "ricochet-robots": "#AB47BC",
    "snake": "#FDD835", "visitall": "#43A047"
}

plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'figure.facecolor': 'white',
})


# ===== LOAD PRE-CALCULATED DATA =====
def load_precalculated():
    """Load all pre-calculated IPC score tables."""
    data = {}
    
    for context in ["Configuration_Sensitivity", "Simulated_Competition"]:
        ctx = {}
        
        # S0
        ctx["S0"] = pd.read_csv(PRECALC_DIR / context / "S0_Baseline_IPC.csv", index_col=0)
        
        # S1 per LLM
        ctx["S1"] = {}
        for llm_name, llm_file in LLM_FILE_MAP.items():
            ctx["S1"][llm_name] = pd.read_csv(
                PRECALC_DIR / context / f"S1_General_{llm_file}.csv", index_col=0
            )
        
        # S2 per LLM
        ctx["S2"] = {}
        for llm_name, llm_file in LLM_FILE_MAP.items():
            ctx["S2"][llm_name] = pd.read_csv(
                PRECALC_DIR / context / f"S2_ArchAware_{llm_file}.csv", index_col=0
            )
        
        # S3
        ctx["S3"] = pd.read_csv(PRECALC_DIR / context / "S3_FeedbackLoop_All_Iterations.csv")
        ctx["S3"]["Score"] = pd.to_numeric(ctx["S3"]["Score"], errors='coerce')
        
        # T* reference
        ctx["T_star"] = pd.read_csv(PRECALC_DIR / context / "T_star_reference.csv")
        
        data[context] = ctx
    
    return data


def load_raw_data():
    """Load raw planner execution data for per-instance analysis."""
    df = pd.read_csv(MAIN_CSV)
    df["LLM_Display"] = df["LLM_Used"].map(LLM_RAW_MAP)
    return df


# ===== HELPER: Extract S2 target-planner IPC per (planner, domain) =====
def get_s2_target_scores(s2_tables):
    """
    From S2 tables (one per LLM), extract the IPC score where the planner
    that RAN matches the planner the domain was PROMPTED FOR.
    Returns a dict: {llm: DataFrame(planners x domains)} for target-only.
    """
    result = {}
    for llm_name, s2_df in s2_tables.items():
        rows = {}
        for planner in PLANNERS:
            row = {}
            for domain in DOMAINS:
                col = f"{domain}_for_{planner}"
                if col in s2_df.columns:
                    val = s2_df.loc[planner, col] if planner in s2_df.index else np.nan
                else:
                    val = np.nan
                row[domain] = val
            rows[planner] = row
        result[llm_name] = pd.DataFrame(rows).T
        result[llm_name].columns.name = None
    return result


# ===== HELPER: Get best S3 score per (planner, domain, llm) =====
def get_s3_best_scores(s3_df):
    """Get best score across all iterations for each (Domain, LLM, Planner)."""
    valid = s3_df.dropna(subset=["Score"])
    if valid.empty:
        return pd.DataFrame()
    return valid.groupby(["Planner", "Domain", "LLM"])["Score"].max().reset_index()


# ===== TABLE G-T1 =====
def compute_table_GT1(data, context_key):
    """G-T1: Global IPC Score — Per Stage x Per Planner (aggregated across LLMs)."""
    print("\n--- Computing Table G-T1 ---")
    ctx = data[context_key]
    
    rows = []
    for planner in PLANNERS:
        # S0: single value per planner (sum across domains)
        s0_ipc = ctx["S0"].loc[planner, "TOTAL"]
        
        # S1: average across LLMs, but BEST is Method 2 (Domain-Level Portfolio)
        s1_values = [ctx["S1"][llm].loc[planner, "TOTAL"] for llm in LLM_NAMES]
        s1_avg = np.mean(s1_values)
        
        s1_best_total = 0.0
        for d in DOMAINS:
            d_vals = [ctx["S1"][llm].loc[planner, d] for llm in LLM_NAMES]
            if any(pd.notna(v) for v in d_vals):
                s1_best_total += np.nanmax(d_vals)
        s1_best = s1_best_total
        s1_best_llm = "Portfolio"
        
        # S2: target-planner only, average across LLMs, but BEST is Method 2
        s2_target = get_s2_target_scores(ctx["S2"])
        s2_totals = []
        for llm_name in LLM_NAMES:
            if llm_name in s2_target:
                total = s2_target[llm_name].loc[planner].sum()
                if not np.isnan(total):
                    s2_totals.append(total)
        s2_avg = np.mean(s2_totals) if s2_totals else np.nan
        
        s2_best_total = 0.0
        for d in DOMAINS:
            d_vals = []
            for llm_name in LLM_NAMES:
                if llm_name in s2_target and planner in s2_target[llm_name].index and d in s2_target[llm_name].columns:
                    v = s2_target[llm_name].loc[planner, d]
                    if not np.isnan(v):
                        d_vals.append(v)
            if d_vals:
                s2_best_total += np.max(d_vals)
        s2_best = s2_best_total if s2_best_total > 0 else np.nan
        
        # S3: best score across all LLMs and iterations for each domain, then sum
        s3_df = ctx["S3"]
        valid_s3 = s3_df[(s3_df["Planner"] == planner)].dropna(subset=["Score"])
        if not valid_s3.empty:
            # Best per domain (across all LLMs and iterations)
            best_per_domain = valid_s3.groupby("Domain")["Score"].max()
            s3_total = sum(best_per_domain.get(d, 0) for d in DOMAINS)
        else:
            s3_total = 0.0
        
        # Best stage
        stage_scores = {"S0": s0_ipc, "S1": s1_best, "S2": s2_best, "S3": s3_total}
        valid_scores = {k: v for k, v in stage_scores.items() if not np.isnan(v)}
        best_stage = max(valid_scores, key=valid_scores.get) if valid_scores else "N/A"
        best_val = max(valid_scores.values()) if valid_scores else np.nan
        delta = best_val - s0_ipc if not np.isnan(best_val) else np.nan
        
        rows.append({
            "Planner": PLANNER_DISPLAY[planner],
            "S0 IPC": round(s0_ipc, 4),
            "S1 IPC (avg)": round(s1_avg, 4),
            "S1 IPC (best)": round(s1_best, 4),
            "S1 Best LLM": s1_best_llm,
            "S2 IPC (avg)": round(s2_avg, 4) if not np.isnan(s2_avg) else "N/A",
            "S2 IPC (best)": round(s2_best, 4) if not np.isnan(s2_best) else "N/A",
            "S3 IPC (best)": round(s3_total, 4),
            "Best Stage": best_stage,
            "Δ Best vs S0": round(delta, 4) if not np.isnan(delta) else "N/A"
        })
    
    # Total row
    s0_total = sum(r["S0 IPC"] for r in rows)
    s1_avg_total = sum(r["S1 IPC (avg)"] for r in rows)
    s1_best_total = sum(r["S1 IPC (best)"] for r in rows)
    s2_avg_total = sum(float(r["S2 IPC (avg)"]) for r in rows if r["S2 IPC (avg)"] != "N/A")
    s2_best_total = sum(float(r["S2 IPC (best)"]) for r in rows if r["S2 IPC (best)"] != "N/A")
    s3_total_all = sum(r["S3 IPC (best)"] for r in rows)
    
    total_scores = {"S0": s0_total, "S1": s1_best_total, "S2": s2_best_total, "S3": s3_total_all}
    best_total_stage = max(total_scores, key=total_scores.get)
    best_total_val = max(total_scores.values())
    
    rows.append({
        "Planner": "**TOTAL**",
        "S0 IPC": round(s0_total, 4),
        "S1 IPC (avg)": round(s1_avg_total, 4),
        "S1 IPC (best)": round(s1_best_total, 4),
        "S1 Best LLM": "—",
        "S2 IPC (avg)": round(s2_avg_total, 4),
        "S2 IPC (best)": round(s2_best_total, 4),
        "S3 IPC (best)": round(s3_total_all, 4),
        "Best Stage": best_total_stage,
        "Δ Best vs S0": round(best_total_val - s0_total, 4)
    })
    
    df = pd.DataFrame(rows)
    return df


# ===== TABLE G-T2 =====
def compute_table_GT2(data, context_key):
    """G-T2: Global IPC Score Per-Planner, Per-LLM, Per-Stage (Detailed)."""
    print("\n--- Computing Table G-T2 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    rows = []
    for planner in PLANNERS:
        s0_ipc = ctx["S0"].loc[planner, "TOTAL"]
        
        for llm in LLM_NAMES:
            # S1
            s1_ipc = ctx["S1"][llm].loc[planner, "TOTAL"]
            
            # S2 target
            if llm in s2_target and planner in s2_target[llm].index:
                s2_vals = s2_target[llm].loc[planner]
                s2_ipc = s2_vals.sum() if not s2_vals.isna().all() else np.nan
            else:
                s2_ipc = np.nan
            
            # S3 best
            s3_df = ctx["S3"]
            s3_valid = s3_df[
                (s3_df["Planner"] == planner) & 
                (s3_df["LLM"] == llm)
            ].dropna(subset=["Score"])
            if not s3_valid.empty:
                s3_per_domain = s3_valid.groupby("Domain")["Score"].max()
                s3_ipc = sum(s3_per_domain.get(d, 0) for d in DOMAINS)
            else:
                s3_ipc = np.nan
            
            # Best stage
            scores = {"S0": s0_ipc, "S1": s1_ipc}
            if not np.isnan(s2_ipc):
                scores["S2"] = s2_ipc
            if not np.isnan(s3_ipc):
                scores["S3"] = s3_ipc
            best_stage = max(scores, key=scores.get)
            cumulative_gain = (s3_ipc - s0_ipc) if not np.isnan(s3_ipc) else "N/A"
            
            rows.append({
                "Planner": PLANNER_DISPLAY[planner],
                "LLM": llm,
                "S0 IPC": round(s0_ipc, 4),
                "S1 IPC": round(s1_ipc, 4),
                "S2 IPC": round(s2_ipc, 4) if not np.isnan(s2_ipc) else "N/A",
                "S3 IPC": round(s3_ipc, 4) if not np.isnan(s3_ipc) else "N/A",
                "Best Stage": best_stage,
                "Gain (S3-S0)": round(cumulative_gain, 4) if isinstance(cumulative_gain, float) else cumulative_gain,
            })
    
    return pd.DataFrame(rows)


# ===== TABLE G-T3 =====
def compute_table_GT3(data, context_key):
    """G-T3: Global IPC Score Per-Planner, Per-Domain, Per-Stage (Averaged across LLMs)."""
    print("\n--- Computing Table G-T3 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    rows = []
    for planner in PLANNERS:
        for domain in DOMAINS:
            # S0
            s0_val = ctx["S0"].loc[planner, domain]
            
            # S1 avg across LLMs
            s1_vals = [ctx["S1"][llm].loc[planner, domain] for llm in LLM_NAMES]
            s1_avg = np.nanmean(s1_vals)
            
            # S2 target avg across LLMs
            s2_vals = []
            for llm in LLM_NAMES:
                if llm in s2_target and planner in s2_target[llm].index and domain in s2_target[llm].columns:
                    v = s2_target[llm].loc[planner, domain]
                    if not np.isnan(v):
                        s2_vals.append(v)
            s2_avg = np.mean(s2_vals) if s2_vals else np.nan
            
            # S3 avg across LLMs (best per LLM)
            s3_df = ctx["S3"]
            s3_valid = s3_df[
                (s3_df["Planner"] == planner) & 
                (s3_df["Domain"] == domain)
            ].dropna(subset=["Score"])
            if not s3_valid.empty:
                s3_per_llm = s3_valid.groupby("LLM")["Score"].max()
                s3_avg = s3_per_llm.mean()
            else:
                s3_avg = np.nan
            
            # Best Stage
            scores = {"S0": s0_val, "S1": s1_avg}
            if not np.isnan(s2_avg):
                scores["S2"] = s2_avg
            if not np.isnan(s3_avg):
                scores["S3"] = s3_avg
            
            valid_scores = {k: v for k, v in scores.items() if not pd.isna(v)}
            if valid_scores:
                best_stage = max(valid_scores, key=valid_scores.get)
            else:
                best_stage = "N/A"
            
            rows.append({
                "Planner": PLANNER_DISPLAY[planner],
                "Domain": domain,
                "S0 IPC": round(s0_val, 4),
                "S1 Avg IPC": round(s1_avg, 4),
                "S2 Avg IPC": round(s2_avg, 4) if not np.isnan(s2_avg) else "N/A",
                "S3 Avg IPC": round(s3_avg, 4) if not np.isnan(s3_avg) else "N/A",
                "Best Stage": best_stage,
            })
    
    return pd.DataFrame(rows)


# ===== TABLE G-T4 =====
def compute_table_GT4(data, raw_df):
    """G-T4: Simulated Competition IPC Scores Per Stage — using per-instance scoring."""
    print("\n--- Computing Table G-T4 ---")
    ctx = data["Simulated_Competition"]
    
    # Load T* reference for simulated competition
    tstar_df = ctx["T_star"]
    
    # Build T* lookup: (domain, instance) -> T*
    tstar_lookup = {}
    for _, row in tstar_df.iterrows():
        key = (row["Domain"], row["Instance"])
        tstar_lookup[key] = row["T_star"]
    
    def ipc_score(runtime, tstar):
        """Compute IPC score for a single instance."""
        if pd.isna(runtime) or pd.isna(tstar):
            return 0.0
        if isinstance(tstar, str) and tstar == "UNSOLVED":
            return 0.0
        tstar = float(tstar)
        if tstar <= 0:
            return 0.0
        if runtime <= 0:
            return 0.0
        ratio = runtime / tstar
        return 1.0 / (1.0 + np.log10(ratio))
    
    def compute_stage_scores(stage_rows):
        """Compute per-instance IPC scores for a set of rows.
        For each (planner, domain, instance), if multiple configs exist,
        take the BEST score (best LLM/iteration)."""
        instance_scores = {}
        for _, row in stage_rows.iterrows():
            key = (row["Planner_Used"], row["Domain_Name"], row["Problem_Instance"])
            domain_inst = (row["Domain_Name"], row["Problem_Instance"])
            
            tstar = tstar_lookup.get(domain_inst)
            if row["Output_Status"] == "SUCCESS" and tstar and tstar != "UNSOLVED":
                score = ipc_score(row["Runtime_wall_s"], float(tstar))
            else:
                score = 0.0
            
            if key not in instance_scores or score > instance_scores[key]:
                instance_scores[key] = score
        
        scores = list(instance_scores.values())
        total = sum(scores) if scores else 0
        mean_val = np.mean(scores) if scores else 0
        median_val = np.median(scores) if scores else 0
        pct_gt0 = (sum(1 for s in scores if s > 0) / len(scores) * 100) if scores else 0
        return total, mean_val, median_val, pct_gt0, len(scores)
    
    # Stage 0
    s0_rows = raw_df[raw_df["Stage"] == "BASELINE"]
    s0_total, s0_mean, s0_median, s0_pct, s0_n = compute_stage_scores(s0_rows)
    
    # Stage 1 (best LLM per instance)
    s1_rows = raw_df[raw_df["Stage"] == "General"]
    s1_total, s1_mean, s1_median, s1_pct, s1_n = compute_stage_scores(s1_rows)
    
    # Stage 2 (target planner runs only)
    s2_rows_aa = raw_df[raw_df["Stage"] == "Arch_Aware"].copy()
    # Filter to target-planner only
    s2_rows_aa["PromptTarget"] = s2_rows_aa["PromptID"].apply(
        lambda x: PROMPTID_TO_PLANNER.get(int(x), None) if pd.notna(x) else None
    )
    s2_target = s2_rows_aa[s2_rows_aa["Planner_Used"] == s2_rows_aa["PromptTarget"]]
    s2_total, s2_mean, s2_median, s2_pct, s2_n = compute_stage_scores(s2_target)
    
    # Stage 3 (best domain per triple = best across all feedback loop iterations)
    s3_rows = raw_df[raw_df["Stage"].str.startswith("Feedback_Loop")]
    s3_total, s3_mean, s3_median, s3_pct, s3_n = compute_stage_scores(s3_rows)
    
    rows = [
        {"Stage": "Stage 0 (Baseline)", "Instances (n)": s0_n, "Total IPC": round(s0_total, 4),
         "Mean IPC": round(s0_mean, 4), "Median IPC": round(s0_median, 4), "% Score > 0": round(s0_pct, 1)},
        {"Stage": "Stage 1 (General, best LLM)", "Instances (n)": s1_n, "Total IPC": round(s1_total, 4),
         "Mean IPC": round(s1_mean, 4), "Median IPC": round(s1_median, 4), "% Score > 0": round(s1_pct, 1)},
        {"Stage": "Stage 2 (Arch-Aware, target)", "Instances (n)": s2_n, "Total IPC": round(s2_total, 4),
         "Mean IPC": round(s2_mean, 4), "Median IPC": round(s2_median, 4), "% Score > 0": round(s2_pct, 1)},
        {"Stage": "Stage 3 (Feedback Loop, best)", "Instances (n)": s3_n, "Total IPC": round(s3_total, 4),
         "Mean IPC": round(s3_mean, 4), "Median IPC": round(s3_median, 4), "% Score > 0": round(s3_pct, 1)},
    ]
    
    return pd.DataFrame(rows)


# ===== TABLE G-T5 =====
def compute_table_GT5(data, raw_df):
    """G-T5: Best Configuration Per Instance — which stage was the best?"""
    print("\n--- Computing Table G-T5 ---")
    ctx = data["Simulated_Competition"]
    tstar_df = ctx["T_star"]
    
    tstar_lookup = {}
    for _, row in tstar_df.iterrows():
        key = (row["Domain"], row["Instance"])
        tstar_lookup[key] = row["T_star"]
    
    def ipc_score(runtime, tstar):
        if pd.isna(runtime) or pd.isna(tstar):
            return 0.0
        if isinstance(tstar, str) and tstar == "UNSOLVED":
            return 0.0
        tstar = float(tstar)
        if tstar <= 0 or runtime <= 0:
            return 0.0
        return 1.0 / (1.0 + np.log10(runtime / tstar))
    
    stage_map = {
        "BASELINE": "Stage 0 (Baseline)",
        "General": "Stage 1 (General Prompt)",
        "Arch_Aware": "Stage 2 (Arch-Aware)",
        "Cross_Test": "Stage 2 (Cross Test)",
        "Feedback_Loop1": "Stage 3 (Feedback Loop)",
        "Feedback_Loop2": "Stage 3 (Feedback Loop)",
        "Feedback_Loop3": "Stage 3 (Feedback Loop)"
    }
    
    # For each (planner, domain, instance), find the stage that produced the best score
    best_stage_per_instance = {}
    
    for _, row in raw_df.iterrows():
        planner = row["Planner_Used"]
        domain = row["Domain_Name"]
        instance = row["Problem_Instance"]
        stage = stage_map.get(row["Stage"], row["Stage"])
        
        key = (planner, domain, instance)
        domain_inst = (domain, instance)
        tstar = tstar_lookup.get(domain_inst)
        
        if row["Output_Status"] == "SUCCESS" and tstar and tstar != "UNSOLVED":
            score = ipc_score(row["Runtime_wall_s"], float(tstar))
        else:
            score = 0.0
        
        if key not in best_stage_per_instance or score > best_stage_per_instance[key][1]:
            best_stage_per_instance[key] = (stage, score)
    
    # Count
    stage_labels = [
        "Unsolvable",
        "Stage 0 (Baseline)",
        "Stage 1 (General Prompt)",
        "Stage 2 (Arch-Aware)",
        "Stage 2 (Cross Test)",
        "Stage 3 (Feedback Loop)"
    ]
    
    stage_counts = {lbl: 0 for lbl in stage_labels}
    for (stage, score) in best_stage_per_instance.values():
        if score == 0.0:
            stage_counts["Unsolvable"] += 1
        elif stage in stage_counts:
            stage_counts[stage] += 1
    
    total = sum(stage_counts.values())
    rows = []
    for stage_label in stage_labels:
        cnt = stage_counts[stage_label]
        pct = round(cnt / total * 100, 1) if total > 0 else 0
        rows.append({
            "Source of Best Performance": stage_label,
            "Count": cnt,
            "out of": total,
            "Percentage": f"{pct}%"
        })
    
    # Also compute per-planner breakdown
    planner_stage_counts = {p: {lbl: 0 for lbl in stage_labels} for p in PLANNERS}
    for (planner, domain, instance), (stage, score) in best_stage_per_instance.items():
        if score == 0.0:
            planner_stage_counts[planner]["Unsolvable"] += 1
        elif stage in planner_stage_counts[planner]:
            planner_stage_counts[planner][stage] += 1
    
    return pd.DataFrame(rows), planner_stage_counts


# ===== TABLE G-T6 =====
def compute_table_GT6(data, context_key):
    """G-T6: Mean IPC Gain vs. Baseline (Per Planner, Per Stage)."""
    print("\n--- Computing Table G-T6 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    rows = []
    for planner in PLANNERS:
        s0_total = ctx["S0"].loc[planner, "TOTAL"]
        
        # S1: Method 2 (Domain-Level Portfolio)
        s1_best_total = 0.0
        for d in DOMAINS:
            d_vals = [ctx["S1"][llm].loc[planner, d] for llm in LLM_NAMES]
            if any(pd.notna(v) for v in d_vals):
                s1_best_total += np.nanmax(d_vals)
        s1_gain = s1_best_total - s0_total
        
        # S2: target planner, Method 2 (Domain-Level Portfolio)
        s2_best_total = 0.0
        for d in DOMAINS:
            d_vals = []
            for llm_name in LLM_NAMES:
                if llm_name in s2_target and planner in s2_target[llm_name].index and d in s2_target[llm_name].columns:
                    v = s2_target[llm_name].loc[planner, d]
                    if not np.isnan(v):
                        d_vals.append(v)
            if d_vals:
                s2_best_total += np.max(d_vals)
        s2_gain = (s2_best_total - s0_total) if s2_best_total > 0 else np.nan
        
        # S3: best per domain across LLMs
        s3_df = ctx["S3"]
        s3_valid = s3_df[s3_df["Planner"] == planner].dropna(subset=["Score"])
        if not s3_valid.empty:
            s3_per_domain = s3_valid.groupby("Domain")["Score"].max()
            s3_total = sum(s3_per_domain.get(d, 0) for d in DOMAINS)
            s3_gain = s3_total - s0_total
        else:
            s3_gain = np.nan
        
        # Progressive?
        vals = [s1_gain]
        if not np.isnan(s2_gain):
            vals.append(s2_gain)
        if not np.isnan(s3_gain):
            vals.append(s3_gain)
        progressive = all(vals[i] > vals[i-1] for i in range(1, len(vals))) if len(vals) > 1 else "N/A"
        
        rows.append({
            "Planner": PLANNER_DISPLAY[planner],
            "S1 Gain vs S0": round(s1_gain, 4),
            "S2 Gain vs S0": round(s2_gain, 4) if not np.isnan(s2_gain) else "N/A",
            "S3 Gain vs S0": round(s3_gain, 4) if not np.isnan(s3_gain) else "N/A",
            "Progressive?": "Yes" if progressive == True else ("No" if progressive == False else "N/A"),
        })
    
    # Overall
    s0_all = sum(ctx["S0"].loc[p, "TOTAL"] for p in PLANNERS)
    
    # S1 Best Overall
    s1_all = 0.0
    for p in PLANNERS:
        for d in DOMAINS:
            d_vals = [ctx["S1"][llm].loc[p, d] for llm in LLM_NAMES]
            if any(pd.notna(v) for v in d_vals):
                s1_all += np.nanmax(d_vals)
                
    # S2 Best Overall
    s2_all = 0.0
    for p in PLANNERS:
        for d in DOMAINS:
            d_vals = []
            for llm_name in LLM_NAMES:
                if llm_name in s2_target and p in s2_target[llm_name].index and d in s2_target[llm_name].columns:
                    v = s2_target[llm_name].loc[p, d]
                    if not np.isnan(v):
                        d_vals.append(v)
            if d_vals:
                s2_all += np.max(d_vals)
    
    s3_all = 0
    for p in PLANNERS:
        s3_valid = ctx["S3"][ctx["S3"]["Planner"] == p].dropna(subset=["Score"])
        if not s3_valid.empty:
            s3_per_domain = s3_valid.groupby("Domain")["Score"].max()
            s3_all += sum(s3_per_domain.get(d, 0) for d in DOMAINS)
    
    rows.append({
        "Planner": "**Overall**",
        "S1 Gain vs S0": round(s1_all - s0_all, 4),
        "S2 Gain vs S0": round(s2_all - s0_all, 4),
        "S3 Gain vs S0": round(s3_all - s0_all, 4),
        "Progressive?": "Yes" if (s2_all - s0_all) > (s1_all - s0_all) and (s3_all - s0_all) > (s2_all - s0_all) else "No",
    })
    
    return pd.DataFrame(rows)


# ===== TABLE G-T7 =====
def compute_table_GT7(data, context_key):
    """G-T7: Mean IPC Gain vs. Baseline (Per Domain, Per Stage)."""
    print("\n--- Computing Table G-T7 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    rows = []
    for domain in DOMAINS:
        # S0: sum across planners for this domain
        s0_val = sum(ctx["S0"].loc[p, domain] for p in PLANNERS)
        
        # S1: Method 2 (Domain-Level Portfolio)
        s1_best_total = 0.0
        for p in PLANNERS:
            d_vals = [ctx["S1"][llm].loc[p, domain] for llm in LLM_NAMES]
            if any(pd.notna(v) for v in d_vals):
                s1_best_total += np.nanmax(d_vals)
        s1_gain = s1_best_total - s0_val
        
        # S2: target planner, Method 2 (Domain-Level Portfolio)
        s2_best_total = 0.0
        for p in PLANNERS:
            d_vals = []
            for llm_name in LLM_NAMES:
                if llm_name in s2_target and p in s2_target[llm_name].index and domain in s2_target[llm_name].columns:
                    v = s2_target[llm_name].loc[p, domain]
                    if not np.isnan(v):
                        d_vals.append(v)
            if d_vals:
                s2_best_total += np.max(d_vals)
        s2_gain = s2_best_total - s0_val
        
        # S3: best per planner across all LLMs
        s3_df = ctx["S3"]
        s3_total = 0
        for p in PLANNERS:
            s3_valid = s3_df[(s3_df["Planner"] == p) & (s3_df["Domain"] == domain)].dropna(subset=["Score"])
            if not s3_valid.empty:
                s3_total += s3_valid["Score"].max()
        s3_gain = s3_total - s0_val
        
        # Progressive?
        vals = [s1_gain]
        if not np.isnan(s2_gain):
            vals.append(s2_gain)
        vals.append(s3_gain)
        progressive = all(vals[i] > vals[i-1] for i in range(1, len(vals))) if len(vals) > 1 else "N/A"
        
        rows.append({
            "Domain": domain,
            "S1 Gain vs S0": round(s1_gain, 4),
            "S2 Gain vs S0": round(s2_gain, 4) if not np.isnan(s2_gain) else "N/A",
            "S3 Gain vs S0": round(s3_gain, 4),
            "Progressive?": "Yes" if progressive == True else ("No" if progressive == False else "N/A"),
        })
    
    return pd.DataFrame(rows)


# ===== ADDITIONAL TABLE: G-T_Extra1 — S2 Full Cross-Test Summary =====
def compute_table_GT_extra1(data, context_key):
    """Extra: S2 IPC including cross-planner results, per LLM summary."""
    print("\n--- Computing Extra Table: S2 Cross-Test Summary ---")
    ctx = data[context_key]
    
    rows = []
    for llm in LLM_NAMES:
        s2_df = ctx["S2"][llm]
        for planner in PLANNERS:
            if planner in s2_df.index:
                target_col = [c for c in s2_df.columns if c.endswith(f"_for_{planner}")]
                target_scores = s2_df.loc[planner, target_col].dropna()
                cross_cols = [c for c in s2_df.columns if not c.endswith(f"_for_{planner}")]
                cross_scores = s2_df.loc[planner, cross_cols].dropna()
                
                rows.append({
                    "LLM": llm,
                    "Planner": PLANNER_DISPLAY[planner],
                    "Target IPC (sum)": round(target_scores.sum(), 4),
                    "Target Domains": len(target_scores),
                    "Cross IPC (sum)": round(cross_scores.sum(), 4),
                    "Cross Domains": len(cross_scores),
                    "Total IPC": round(target_scores.sum() + cross_scores.sum(), 4),
                })
    
    return pd.DataFrame(rows)


# ==========================================================================
# GRAPHS
# ==========================================================================

def plot_G_G1(data, context_key):
    """G-G1: Grouped Bar Chart — Global IPC Score by Stage × Planner."""
    print("\n--- Plotting G-G1 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    stages = ["S0", "S1", "S2", "S3"]
    planner_scores = {}
    
    for planner in PLANNERS:
        scores = []
        # S0
        scores.append(ctx["S0"].loc[planner, "TOTAL"])
        # S1 avg
        s1 = np.mean([ctx["S1"][llm].loc[planner, "TOTAL"] for llm in LLM_NAMES])
        scores.append(s1)
        # S2 target avg
        s2_vals = []
        for llm in LLM_NAMES:
            if llm in s2_target and planner in s2_target[llm].index:
                v = s2_target[llm].loc[planner].sum()
                if not np.isnan(v):
                    s2_vals.append(v)
        scores.append(np.mean(s2_vals) if s2_vals else 0)
        # S3 best per domain
        s3_valid = ctx["S3"][ctx["S3"]["Planner"] == planner].dropna(subset=["Score"])
        if not s3_valid.empty:
            s3_total = sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS)
        else:
            s3_total = 0
        scores.append(s3_total)
        planner_scores[planner] = scores
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(PLANNERS))
    width = 0.18
    
    for i, stage in enumerate(stages):
        vals = [planner_scores[p][i] for p in PLANNERS]
        bars = ax.bar(x + i * width, vals, width, label=stage,
                     color=STAGE_COLORS[stage], edgecolor='white', linewidth=0.5)
        # Add value labels
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                   f'{val:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax.set_xlabel("Planner")
    ax.set_ylabel("Total IPC Score")
    ax.set_title(f"Global IPC Score by Stage × Planner\n({context_key.replace('_', ' ')})", fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([PLANNER_DISPLAY[p] for p in PLANNERS])
    ax.legend(title="Stage")
    ax.set_ylim(0, max(max(v) for v in planner_scores.values()) * 1.15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ctx_short = "CS" if "Configuration" in context_key else "SC"
    plt.savefig(OUTPUT_DIR / "graphs" / f"G_G1_Grouped_Bar_Stage_x_Planner_{ctx_short}.png")
    plt.close()


def plot_G_G2(data, context_key):
    """G-G2: Line Chart — IPC Score Progression Across Stages (Per Planner)."""
    print("\n--- Plotting G-G2 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    fig, ax = plt.subplots(figsize=(10, 7))
    stages_x = [0, 1, 2, 3]
    
    for planner in PLANNERS:
        scores = []
        # S0
        scores.append(ctx["S0"].loc[planner, "TOTAL"])
        # S1 avg
        scores.append(np.mean([ctx["S1"][llm].loc[planner, "TOTAL"] for llm in LLM_NAMES]))
        # S2 target avg
        s2_vals = []
        for llm in LLM_NAMES:
            if llm in s2_target and planner in s2_target[llm].index:
                v = s2_target[llm].loc[planner].sum()
                if not np.isnan(v):
                    s2_vals.append(v)
        scores.append(np.mean(s2_vals) if s2_vals else np.nan)
        # S3 best
        s3_valid = ctx["S3"][ctx["S3"]["Planner"] == planner].dropna(subset=["Score"])
        if not s3_valid.empty:
            scores.append(sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS))
        else:
            scores.append(np.nan)
        
        ax.plot(stages_x, scores, marker='o', linewidth=2.5, markersize=8,
               label=PLANNER_DISPLAY[planner], color=PLANNER_COLORS[planner])
        # Annotate
        for xi, val in zip(stages_x, scores):
            if not np.isnan(val):
                ax.annotate(f'{val:.1f}', (xi, val), textcoords="offset points",
                           xytext=(0, 10), ha='center', fontsize=8, fontweight='bold')
    
    ax.set_xlabel("Stage")
    ax.set_ylabel("Total IPC Score")
    ax.set_title(f"IPC Score Progression Across Stages (Per Planner)\n({context_key.replace('_', ' ')})",
                fontweight='bold')
    ax.set_xticks(stages_x)
    ax.set_xticklabels(["S0\n(Baseline)", "S1\n(General)", "S2\n(Arch-Aware)", "S3\n(Feedback)"])
    ax.legend(title="Planner", loc='best')
    ax.grid(alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ctx_short = "CS" if "Configuration" in context_key else "SC"
    plt.savefig(OUTPUT_DIR / "graphs" / f"G_G2_Line_Progression_Per_Planner_{ctx_short}.png")
    plt.close()


def plot_G_G3(data, context_key):
    """G-G3: Line Chart — IPC Score Progression Across Stages (Per Domain)."""
    print("\n--- Plotting G-G3 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    fig, ax = plt.subplots(figsize=(10, 7))
    stages_x = [0, 1, 2, 3]
    
    for domain in DOMAINS:
        scores = []
        
        # S0: sum across planners
        s0_val = sum(ctx["S0"].loc[p, domain] for p in PLANNERS)
        scores.append(s0_val)
        
        # S1: avg across LLMs, sum across planners
        s1_vals = [sum(ctx["S1"][llm].loc[p, domain] for p in PLANNERS) for llm in LLM_NAMES]
        scores.append(np.mean(s1_vals))
        
        # S2: target planner, avg across LLMs
        s2_vals = []
        for llm in LLM_NAMES:
            llm_total = 0
            valid = False
            for p in PLANNERS:
                if llm in s2_target and p in s2_target[llm].index and domain in s2_target[llm].columns:
                    v = s2_target[llm].loc[p, domain]
                    if not np.isnan(v):
                        llm_total += v
                        valid = True
            if valid:
                s2_vals.append(llm_total)
        scores.append(np.mean(s2_vals) if s2_vals else np.nan)
        
        # S3: best per planner
        s3_total = 0
        for p in PLANNERS:
            s3_valid = ctx["S3"][(ctx["S3"]["Planner"] == p) & (ctx["S3"]["Domain"] == domain)].dropna(subset=["Score"])
            if not s3_valid.empty:
                s3_total += s3_valid["Score"].max()
        scores.append(s3_total)
        
        ax.plot(stages_x, scores, marker='s', linewidth=2.5, markersize=8,
               label=domain.title(), color=DOMAIN_COLORS[domain])
    
    ax.set_xlabel("Stage")
    ax.set_ylabel("Total IPC Score (summed across planners)")
    ax.set_title(f"IPC Score Progression Across Stages (Per Domain)\n({context_key.replace('_', ' ')})",
                fontweight='bold')
    ax.set_xticks(stages_x)
    ax.set_xticklabels(["S0\n(Baseline)", "S1\n(General)", "S2\n(Arch-Aware)", "S3\n(Feedback)"])
    ax.legend(title="Domain", loc='best')
    ax.grid(alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ctx_short = "CS" if "Configuration" in context_key else "SC"
    plt.savefig(OUTPUT_DIR / "graphs" / f"G_G3_Line_Progression_Per_Domain_{ctx_short}.png")
    plt.close()


def plot_G_G4(planner_stage_counts):
    """G-G4: Stacked Bar — Source of Best Performance (per-planner breakdown)."""
    print("\n--- Plotting G-G4 ---")
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    planners_display = [PLANNER_DISPLAY[p] for p in PLANNERS]
    s0_vals = [planner_stage_counts[p]["Stage 0 (Baseline)"] for p in PLANNERS]
    s1_vals = [planner_stage_counts[p]["Stage 1 (General Prompt)"] for p in PLANNERS]
    s2_vals = [planner_stage_counts[p]["Stage 2 (Arch-Aware)"] for p in PLANNERS]
    s2ct_vals = [planner_stage_counts[p]["Stage 2 (Cross Test)"] for p in PLANNERS]
    s3_vals = [planner_stage_counts[p]["Stage 3 (Feedback Loop)"] for p in PLANNERS]
    uns_vals = [planner_stage_counts[p]["Unsolvable"] for p in PLANNERS]
    
    x = np.arange(len(PLANNERS))
    width = 0.55
    
    b1 = ax.bar(x, s0_vals, width, label="S0 (Baseline)", color=STAGE_COLORS["S0"])
    b2 = ax.bar(x, s1_vals, width, bottom=s0_vals, label="S1 (General)", color=STAGE_COLORS["S1"])
    b3 = ax.bar(x, s2_vals, width, bottom=[s0+s1 for s0, s1 in zip(s0_vals, s1_vals)],
               label="S2 (Arch-Aware)", color=STAGE_COLORS["S2"])
    b4 = ax.bar(x, s2ct_vals, width, bottom=[s0+s1+s2 for s0, s1, s2 in zip(s0_vals, s1_vals, s2_vals)],
               label="S2 (Cross Test)", color="#9B59B6")  # Purple
    b5 = ax.bar(x, s3_vals, width,
               bottom=[s0+s1+s2+s2ct for s0, s1, s2, s2ct in zip(s0_vals, s1_vals, s2_vals, s2ct_vals)],
               label="S3 (Feedback)", color=STAGE_COLORS["S3"])
    b6 = ax.bar(x, uns_vals, width,
               bottom=[s0+s1+s2+s2ct+s3 for s0, s1, s2, s2ct, s3 in zip(s0_vals, s1_vals, s2_vals, s2ct_vals, s3_vals)],
               label="Unsolvable", color="#7F8C8D")  # Gray
    
    # Add totals on top
    for i, p in enumerate(PLANNERS):
        total = sum(planner_stage_counts[p].values())
        ax.text(i, total + 0.5, str(total), ha='center', va='bottom', fontweight='bold')
    
    ax.set_xlabel("Planner")
    ax.set_ylabel("Number of Instances Where Stage Was Best")
    ax.set_title("Source of Best IPC Performance\n(per planner, Simulated Competition)", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(planners_display)
    ax.legend(title="Best Stage")
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.savefig(OUTPUT_DIR / "graphs" / "G_G4_Stacked_Bar_Best_Source.png")
    plt.close()


def plot_G_G5(data, context_key):
    """G-G5: Heatmap — Global IPC Gain vs. Baseline (Planner × Domain)."""
    print("\n--- Plotting G-G5 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    gain_matrix = np.zeros((len(DOMAINS), len(PLANNERS)))
    annotation_matrix = [["" for _ in PLANNERS] for _ in DOMAINS]
    
    for di, domain in enumerate(DOMAINS):
        for pi, planner in enumerate(PLANNERS):
            s0_val = ctx["S0"].loc[planner, domain]
            
            # S1 best
            s1_best = max(ctx["S1"][llm].loc[planner, domain] for llm in LLM_NAMES)
            
            # S2 target best
            s2_vals = []
            for llm in LLM_NAMES:
                if llm in s2_target and planner in s2_target[llm].index and domain in s2_target[llm].columns:
                    v = s2_target[llm].loc[planner, domain]
                    if not np.isnan(v):
                        s2_vals.append(v)
            s2_best = max(s2_vals) if s2_vals else -999
            
            # S3 best
            s3_valid = ctx["S3"][(ctx["S3"]["Planner"] == planner) & (ctx["S3"]["Domain"] == domain)].dropna(subset=["Score"])
            s3_best = s3_valid["Score"].max() if not s3_valid.empty else -999
            
            # Find best gain
            stage_gains = {
                "S1": s1_best - s0_val,
                "S2": s2_best - s0_val if s2_best > -999 else -999,
                "S3": s3_best - s0_val if s3_best > -999 else -999,
            }
            valid_gains = {k: v for k, v in stage_gains.items() if v > -999}
            if valid_gains:
                best_stage = max(valid_gains, key=valid_gains.get)
                best_gain = valid_gains[best_stage]
            else:
                best_stage = "—"
                best_gain = 0
            
            gain_matrix[di][pi] = best_gain
            annotation_matrix[di][pi] = f"{best_gain:+.2f}\n({best_stage})"
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Custom diverging colormap
    max_abs = max(abs(gain_matrix.min()), abs(gain_matrix.max()))
    im = ax.imshow(gain_matrix, cmap='RdYlGn', aspect='auto',
                   vmin=-max_abs, vmax=max_abs)
    
    ax.set_xticks(range(len(PLANNERS)))
    ax.set_xticklabels([PLANNER_DISPLAY[p] for p in PLANNERS])
    ax.set_yticks(range(len(DOMAINS)))
    ax.set_yticklabels([d.title() for d in DOMAINS])
    
    # Add annotations
    for di in range(len(DOMAINS)):
        for pi in range(len(PLANNERS)):
            color = 'black' if abs(gain_matrix[di][pi]) < max_abs * 0.6 else 'white'
            ax.text(pi, di, annotation_matrix[di][pi], ha='center', va='center',
                   fontsize=9, fontweight='bold', color=color)
    
    plt.colorbar(im, ax=ax, label="IPC Gain vs. Baseline", shrink=0.8)
    ax.set_title(f"Best IPC Gain vs. Baseline (Domain × Planner)\n({context_key.replace('_', ' ')})",
                fontweight='bold')
    
    ctx_short = "CS" if "Configuration" in context_key else "SC"
    plt.savefig(OUTPUT_DIR / "graphs" / f"G_G5_Heatmap_Gain_vs_Baseline_{ctx_short}.png")
    plt.close()


def plot_G_G6(data, context_key):
    """G-G6: Radar/Spider Chart — Multi-Metric Stage Comparison (Per Planner)."""
    print("\n--- Plotting G-G6 ---")
    ctx = data[context_key]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 14), subplot_kw=dict(polar=True))
    axes = axes.flatten()
    
    metrics = ["IPC Score", "Solve Rate (%)", "Avg IPC/Instance"]
    n_metrics = len(metrics)
    angles = np.linspace(0, 2*np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon
    
    for idx, planner in enumerate(PLANNERS):
        ax = axes[idx]
        s0_total = ctx["S0"].loc[planner, "TOTAL"]
        
        # S0
        s0_solve = sum(1 for d in DOMAINS for _ in [ctx["S0"].loc[planner, d]] if _ > 0) / len(DOMAINS) * 100
        s0_avg_per_inst = s0_total / (len(DOMAINS) * len(INSTANCES)) * 100  # normalize
        
        # S1
        s1_total = np.mean([ctx["S1"][llm].loc[planner, "TOTAL"] for llm in LLM_NAMES])
        s1_solve = sum(1 for d in DOMAINS for llm in LLM_NAMES if ctx["S1"][llm].loc[planner, d] > 0) / (len(DOMAINS)*len(LLM_NAMES)) * 100
        s1_avg_per_inst = s1_total / (len(DOMAINS) * len(INSTANCES)) * 100
        
        # S2
        s2_vals = []
        for llm in LLM_NAMES:
            if llm in s2_target and planner in s2_target[llm].index:
                v = s2_target[llm].loc[planner].sum()
                if not np.isnan(v):
                    s2_vals.append(v)
        s2_total = np.mean(s2_vals) if s2_vals else 0
        s2_solve_count = sum(1 for llm in LLM_NAMES if llm in s2_target and planner in s2_target[llm].index
                           for d in DOMAINS if d in s2_target[llm].columns and not np.isnan(s2_target[llm].loc[planner, d]) and s2_target[llm].loc[planner, d] > 0)
        s2_solve_total = sum(1 for llm in LLM_NAMES if llm in s2_target and planner in s2_target[llm].index
                           for d in DOMAINS if d in s2_target[llm].columns and not np.isnan(s2_target[llm].loc[planner, d]))
        s2_solve = (s2_solve_count / s2_solve_total * 100) if s2_solve_total > 0 else 0
        s2_avg_per_inst = s2_total / (len(DOMAINS) * len(INSTANCES)) * 100
        
        # S3
        s3_valid = ctx["S3"][ctx["S3"]["Planner"] == planner].dropna(subset=["Score"])
        if not s3_valid.empty:
            s3_total = sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS)
            s3_domains_with_score = sum(1 for d in DOMAINS if s3_valid[s3_valid["Domain"] == d]["Score"].max() > 0)
            s3_solve = s3_domains_with_score / len(DOMAINS) * 100
        else:
            s3_total = 0
            s3_solve = 0
        s3_avg_per_inst = s3_total / (len(DOMAINS) * len(INSTANCES)) * 100
        
        # Normalize all metrics to 0-100 scale for radar
        max_ipc = max(s0_total, s1_total, s2_total, s3_total, 1)
        
        for stage_label, stage_color, vals in [
            ("S0", STAGE_COLORS["S0"], [s0_total/max_ipc*100, s0_solve, s0_avg_per_inst]),
            ("S1", STAGE_COLORS["S1"], [s1_total/max_ipc*100, s1_solve, s1_avg_per_inst]),
            ("S2", STAGE_COLORS["S2"], [s2_total/max_ipc*100, s2_solve, s2_avg_per_inst]),
            ("S3", STAGE_COLORS["S3"], [s3_total/max_ipc*100, s3_solve, s3_avg_per_inst]),
        ]:
            vals_closed = vals + vals[:1]
            ax.plot(angles, vals_closed, 'o-', linewidth=2, label=stage_label, color=stage_color)
            ax.fill(angles, vals_closed, alpha=0.1, color=stage_color)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=9)
        ax.set_title(PLANNER_DISPLAY[planner], fontsize=13, fontweight='bold', pad=20)
        ax.set_ylim(0, 110)
        if idx == 0:
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    
    plt.suptitle(f"Multi-Metric Stage Comparison (Radar)\n({context_key.replace('_', ' ')})",
                fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    ctx_short = "CS" if "Configuration" in context_key else "SC"
    plt.savefig(OUTPUT_DIR / "graphs" / f"G_G6_Radar_Multi_Metric_{ctx_short}.png")
    plt.close()


# ===== ADDITIONAL GRAPH: Summary Dashboard =====
def plot_summary_dashboard(data):
    """Additional: Combined summary figure showing headline results."""
    print("\n--- Plotting Summary Dashboard ---")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Panel 1: Config Sensitivity totals
    ax = axes[0, 0]
    ctx = data["Configuration_Sensitivity"]
    s2_target = get_s2_target_scores(ctx["S2"])
    
    stage_totals = {}
    for stage_label, stage_key in [("S0", "S0"), ("S1", "S1"), ("S2", "S2"), ("S3", "S3")]:
        total = 0
        for p in PLANNERS:
            if stage_key == "S0":
                total += ctx["S0"].loc[p, "TOTAL"]
            elif stage_key == "S1":
                total += np.mean([ctx["S1"][llm].loc[p, "TOTAL"] for llm in LLM_NAMES])
            elif stage_key == "S2":
                s2v = []
                for llm in LLM_NAMES:
                    if llm in s2_target and p in s2_target[llm].index:
                        v = s2_target[llm].loc[p].sum()
                        if not np.isnan(v):
                            s2v.append(v)
                total += np.mean(s2v) if s2v else 0
            elif stage_key == "S3":
                s3_valid = ctx["S3"][ctx["S3"]["Planner"] == p].dropna(subset=["Score"])
                if not s3_valid.empty:
                    total += sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS)
        stage_totals[stage_label] = total
    
    bars = ax.bar(stage_totals.keys(), stage_totals.values(),
                 color=[STAGE_COLORS[s] for s in stage_totals.keys()],
                 edgecolor='white', linewidth=1)
    for bar, val in zip(bars, stage_totals.values()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
               f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    ax.set_title("Config Sensitivity: Total IPC by Stage", fontweight='bold')
    ax.set_ylabel("Total IPC Score")
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Panel 2: Simulated Competition totals
    ax = axes[0, 1]
    ctx_sc = data["Simulated_Competition"]
    s2_target_sc = get_s2_target_scores(ctx_sc["S2"])
    
    stage_totals_sc = {}
    for stage_label, stage_key in [("S0", "S0"), ("S1", "S1"), ("S2", "S2"), ("S3", "S3")]:
        total = 0
        for p in PLANNERS:
            if stage_key == "S0":
                total += ctx_sc["S0"].loc[p, "TOTAL"]
            elif stage_key == "S1":
                total += np.mean([ctx_sc["S1"][llm].loc[p, "TOTAL"] for llm in LLM_NAMES])
            elif stage_key == "S2":
                s2v = []
                for llm in LLM_NAMES:
                    if llm in s2_target_sc and p in s2_target_sc[llm].index:
                        v = s2_target_sc[llm].loc[p].sum()
                        if not np.isnan(v):
                            s2v.append(v)
                total += np.mean(s2v) if s2v else 0
            elif stage_key == "S3":
                s3_valid = ctx_sc["S3"][ctx_sc["S3"]["Planner"] == p].dropna(subset=["Score"])
                if not s3_valid.empty:
                    total += sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS)
        stage_totals_sc[stage_label] = total
    
    bars = ax.bar(stage_totals_sc.keys(), stage_totals_sc.values(),
                 color=[STAGE_COLORS[s] for s in stage_totals_sc.keys()],
                 edgecolor='white', linewidth=1)
    for bar, val in zip(bars, stage_totals_sc.values()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
               f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    ax.set_title("Simulated Competition: Total IPC by Stage", fontweight='bold')
    ax.set_ylabel("Total IPC Score")
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Panel 3: Gain vs S0 (per planner, Config Sensitivity)
    ax = axes[1, 0]
    s2_target_cs = get_s2_target_scores(ctx["S2"])
    for planner in PLANNERS:
        gains = [0]  # S0 gain = 0
        s0 = ctx["S0"].loc[planner, "TOTAL"]
        
        s1_gain = np.mean([ctx["S1"][llm].loc[planner, "TOTAL"] for llm in LLM_NAMES]) - s0
        gains.append(s1_gain)
        
        s2v = []
        for llm in LLM_NAMES:
            if llm in s2_target_cs and planner in s2_target_cs[llm].index:
                v = s2_target_cs[llm].loc[planner].sum()
                if not np.isnan(v):
                    s2v.append(v)
        s2_gain = (np.mean(s2v) - s0) if s2v else 0
        gains.append(s2_gain)
        
        s3_valid = ctx["S3"][ctx["S3"]["Planner"] == planner].dropna(subset=["Score"])
        if not s3_valid.empty:
            s3_total = sum(s3_valid.groupby("Domain")["Score"].max().get(d, 0) for d in DOMAINS)
            s3_gain = s3_total - s0
        else:
            s3_gain = 0
        gains.append(s3_gain)
        
        ax.plot([0, 1, 2, 3], gains, marker='o', linewidth=2, label=PLANNER_DISPLAY[planner],
               color=PLANNER_COLORS[planner])
    
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["S0", "S1", "S2", "S3"])
    ax.set_title("IPC Gain vs. Baseline (Config Sensitivity)", fontweight='bold')
    ax.set_ylabel("IPC Gain")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Panel 4: Gain vs S0 per domain
    ax = axes[1, 1]
    for domain in DOMAINS:
        gains = [0]
        s0 = sum(ctx["S0"].loc[p, domain] for p in PLANNERS)
        
        s1 = np.mean([sum(ctx["S1"][llm].loc[p, domain] for p in PLANNERS) for llm in LLM_NAMES])
        gains.append(s1 - s0)
        
        s2v = []
        for llm in LLM_NAMES:
            lt = 0
            valid = False
            for p in PLANNERS:
                if llm in s2_target_cs and p in s2_target_cs[llm].index and domain in s2_target_cs[llm].columns:
                    v = s2_target_cs[llm].loc[p, domain]
                    if not np.isnan(v):
                        lt += v
                        valid = True
            if valid:
                s2v.append(lt)
        gains.append((np.mean(s2v) - s0) if s2v else 0)
        
        s3_total = 0
        for p in PLANNERS:
            s3_valid = ctx["S3"][(ctx["S3"]["Planner"] == p) & (ctx["S3"]["Domain"] == domain)].dropna(subset=["Score"])
            if not s3_valid.empty:
                s3_total += s3_valid["Score"].max()
        gains.append(s3_total - s0)
        
        ax.plot([0, 1, 2, 3], gains, marker='s', linewidth=2, label=domain.title(),
               color=DOMAIN_COLORS[domain])
    
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["S0", "S1", "S2", "S3"])
    ax.set_title("IPC Gain vs. Baseline per Domain (Config Sensitivity)", fontweight='bold')
    ax.set_ylabel("IPC Gain")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.suptitle("Section 1 — Global IPC Score Analysis Dashboard", fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "graphs" / "G_Summary_Dashboard.png")
    plt.close()


# ===== RENDER TABLE TO IMAGE =====
def render_table_image(df, output_path, title=""):
    """Render a DataFrame as a styled table image."""
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')
    
    cell_text = df.values.tolist()
    col_labels = df.columns.tolist()
    
    table = ax.table(cellText=cell_text, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.8, 1.8)
    
    # Style header
    for j in range(len(col_labels)):
        table[0, j].set_facecolor('#2C3E50')
        table[0, j].set_text_props(color='white', fontweight='bold')
    
    # Alternate row colors
    for i in range(len(cell_text)):
        for j in range(len(col_labels)):
            if i % 2 == 0:
                table[i+1, j].set_facecolor('#F8F9FA')
            else:
                table[i+1, j].set_facecolor('#FFFFFF')
    
    num_cols = len(col_labels)
    num_rows = len(cell_text)
    fig.set_size_inches(max(num_cols * 2.0, 10), max(num_rows * 0.6, 3))
    
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=max(20, num_rows * 12))
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()


# ===== GENERATE SUMMARY REPORT =====
def generate_report(tables_dict):
    """Generate a markdown summary report for Section 1."""
    print("\n--- Generating Summary Report ---")
    
    lines = []
    lines.append("# Section 1: Global IPC Score Analysis — Results Report")
    lines.append("")
    lines.append("> **Generated:** 2026-06-06  ")
    lines.append("> **Context:** Cross-Stage Comparative Analysis  ")
    lines.append("> **Data Source:** Pre-calculated global IPC scores from `1_Global_IPC_Score (Most Important)/tables/`")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    lines.append("## Methodological Note: Method 2 (Domain-Level Portfolio)")
    lines.append("> **Note:** For the `(best)` columns in Stage 1 and Stage 2 (and the Mean Gain tables G-T6 and G-T7), this analysis uses **Method 2 (The Best Domain-Level Portfolio)**.")
    lines.append("> Instead of selecting a single best LLM overall, it calculates the theoretical maximum by taking the best score achieved by *any* LLM for each specific domain, and summing those up. This ensures a true apples-to-apples comparison with Stage 3 (Feedback Loop), which also uses a portfolio/best-iteration approach. It creates a strict ablation study, neutralizing the confounding variable of 'number of attempts', and evaluates the pure theoretical maximum of each prompting strategy.")
    lines.append("")
    
    # G-T1 summary
    lines.append("## Table G-T1: Global IPC Score — Per Stage x Per Planner")
    lines.append("")
    lines.append("### Configuration Sensitivity")
    lines.append("")
    gt1_cs = tables_dict["GT1_CS"]
    lines.append(gt1_cs.to_markdown(index=False))
    lines.append("")
    lines.append("### Simulated Competition")
    lines.append("")
    gt1_sc = tables_dict["GT1_SC"]
    lines.append(gt1_sc.to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # G-T4 summary
    lines.append("## Table G-T4: Simulated Competition IPC Scores Per Stage")
    lines.append("")
    lines.append("> **Methodological Note on Stage Scoring:**")
    lines.append("> To calculate the 'Total IPC' for Stage 1, Stage 2, and Stage 3 in the Simulated Competition context, the script evaluates performance on a **per-instance portfolio basis**:")
    lines.append("> 1. **Group by Unique Triples**: The execution data is grouped by unique combinations of `(Planner, Domain, Instance)`, totaling 300 instances (4 planners × 5 domains × 15 instances).")
    lines.append("> 2. **Evaluate all Candidates**: For each specific triple (e.g., `BFWS`, `barman`, `instance_1`), multiple PDDL models were generated (e.g., 4 models in Stage 1, one from each LLM; or 5 iterations in Stage 3).")
    lines.append("> 3. **Take the Maximum**: Because this is a 'Simulated Competition' (where the competition framework takes the best result from all submissions), the script selects the `max()` IPC score out of those candidate LLMs/iterations for that specific instance.")
    lines.append("> 4. **Sum the 300 Bests**: Finally, it adds up these 300 'best' per-instance scores to yield the Total IPC for the Stage.")
    lines.append("")
    gt4 = tables_dict.get("GT4")
    if gt4 is not None:
        lines.append(gt4.to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # G-T5 summary
    lines.append("## Table G-T5: Best Configuration Per Instance (Simulated Competition)")
    lines.append("")
    lines.append("> This is a **headline result** — it directly answers 'Did our approach beat the baseline?'")
    lines.append("")
    gt5 = tables_dict["GT5"]
    lines.append(gt5.to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # G-T6 summary
    lines.append("## Table G-T6: IPC Gain vs. Baseline (Per Planner)")
    lines.append("")
    lines.append("### Configuration Sensitivity")
    lines.append("")
    gt6 = tables_dict["GT6_CS"]
    lines.append(gt6.to_markdown(index=False))
    lines.append("")
    lines.append("### Simulated Competition")
    lines.append("")
    gt6_sc = tables_dict["GT6_SC"]
    lines.append(gt6_sc.to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # G-T7 summary
    lines.append("## Table G-T7: IPC Gain vs. Baseline (Per Domain)")
    lines.append("")
    lines.append("### Configuration Sensitivity")
    lines.append("")
    gt7 = tables_dict["GT7_CS"]
    lines.append(gt7.to_markdown(index=False))
    lines.append("")
    lines.append("### Simulated Competition")
    lines.append("")
    gt7_sc = tables_dict["GT7_SC"]
    lines.append(gt7_sc.to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    lines.append("## Output Files")
    lines.append("")
    lines.append("### Tables (CSV + PNG)")
    lines.append("All tables are saved in `section1_analysis/tables/`")
    lines.append("")
    lines.append("### Graphs")
    lines.append("All graphs are saved in `section1_analysis/graphs/`")
    lines.append("")
    
    report_path = OUTPUT_DIR / "Section1_Results_Report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved to: {report_path}")


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("=" * 70)
    print("SECTION 1: GLOBAL IPC SCORE ANALYSIS")
    print("=" * 70)
    
    # Load data
    print("\nLoading pre-calculated data...")
    data = load_precalculated()
    print("Loading raw execution data...")
    raw_df = load_raw_data()
    print(f"Raw data: {len(raw_df)} rows")
    
    tables_dict = {}
    
    # ===== TABLES =====
    for context in ["Configuration_Sensitivity", "Simulated_Competition"]:
        ctx_short = "CS" if "Configuration" in context else "SC"
        print(f"\n{'='*50}")
        print(f"CONTEXT: {context}")
        print(f"{'='*50}")
        
        # G-T1
        gt1 = compute_table_GT1(data, context)
        gt1.to_csv(OUTPUT_DIR / "tables" / f"G_T1_IPC_Per_Stage_Planner_{ctx_short}.csv", index=False)
        render_table_image(gt1, OUTPUT_DIR / "tables" / f"G_T1_IPC_Per_Stage_Planner_{ctx_short}.png",
                          f"G-T1: Global IPC Score — Per Stage × Per Planner ({context.replace('_', ' ')})")
        tables_dict[f"GT1_{ctx_short}"] = gt1
        print(f"  G-T1 saved ({ctx_short})")
        
        # G-T2
        gt2 = compute_table_GT2(data, context)
        gt2.to_csv(OUTPUT_DIR / "tables" / f"G_T2_IPC_Detailed_Planner_LLM_{ctx_short}.csv", index=False)
        render_table_image(gt2, OUTPUT_DIR / "tables" / f"G_T2_IPC_Detailed_Planner_LLM_{ctx_short}.png",
                          f"G-T2: Detailed IPC Per Planner × LLM ({context.replace('_', ' ')})")
        tables_dict[f"GT2_{ctx_short}"] = gt2
        print(f"  G-T2 saved ({ctx_short})")
        
        # G-T3
        gt3 = compute_table_GT3(data, context)
        gt3.to_csv(OUTPUT_DIR / "tables" / f"G_T3_IPC_Planner_Domain_{ctx_short}.csv", index=False)
        render_table_image(gt3, OUTPUT_DIR / "tables" / f"G_T3_IPC_Planner_Domain_{ctx_short}.png",
                          f"G-T3: IPC Per Planner × Domain ({context.replace('_', ' ')})")
        tables_dict[f"GT3_{ctx_short}"] = gt3
        print(f"  G-T3 saved ({ctx_short})")
        
        # G-T6
        gt6 = compute_table_GT6(data, context)
        gt6.to_csv(OUTPUT_DIR / "tables" / f"G_T6_IPC_Gain_Per_Planner_{ctx_short}.csv", index=False)
        render_table_image(gt6, OUTPUT_DIR / "tables" / f"G_T6_IPC_Gain_Per_Planner_{ctx_short}.png",
                          f"G-T6: IPC Gain vs. Baseline Per Planner ({context.replace('_', ' ')})")
        tables_dict[f"GT6_{ctx_short}"] = gt6
        print(f"  G-T6 saved ({ctx_short})")
        
        # G-T7
        gt7 = compute_table_GT7(data, context)
        gt7.to_csv(OUTPUT_DIR / "tables" / f"G_T7_IPC_Gain_Per_Domain_{ctx_short}.csv", index=False)
        render_table_image(gt7, OUTPUT_DIR / "tables" / f"G_T7_IPC_Gain_Per_Domain_{ctx_short}.png",
                          f"G-T7: IPC Gain vs. Baseline Per Domain ({context.replace('_', ' ')})")
        tables_dict[f"GT7_{ctx_short}"] = gt7
        print(f"  G-T7 saved ({ctx_short})")
        
        # Extra: S2 Cross-Test Summary
        gt_extra = compute_table_GT_extra1(data, context)
        gt_extra.to_csv(OUTPUT_DIR / "tables" / f"G_T_Extra_S2_CrossTest_Summary_{ctx_short}.csv", index=False)
        render_table_image(gt_extra, OUTPUT_DIR / "tables" / f"G_T_Extra_S2_CrossTest_Summary_{ctx_short}.png",
                          f"S2 Cross-Test Summary ({context.replace('_', ' ')})")
        print(f"  Extra S2 table saved ({ctx_short})")
        
        # Graphs
        plot_G_G1(data, context)
        print(f"  G-G1 saved ({ctx_short})")
        
        plot_G_G2(data, context)
        print(f"  G-G2 saved ({ctx_short})")
        
        plot_G_G3(data, context)
        print(f"  G-G3 saved ({ctx_short})")
        
        plot_G_G5(data, context)
        print(f"  G-G5 saved ({ctx_short})")
        
        plot_G_G6(data, context)
        print(f"  G-G6 saved ({ctx_short})")
    
    # Simulated Competition specific tables
    gt4 = compute_table_GT4(data, raw_df)
    gt4.to_csv(OUTPUT_DIR / "tables" / "G_T4_Simulated_Competition_Per_Stage.csv", index=False)
    render_table_image(gt4, OUTPUT_DIR / "tables" / "G_T4_Simulated_Competition_Per_Stage.png",
                      "G-T4: Simulated Competition IPC Scores Per Stage")
    tables_dict["GT4"] = gt4
    print("  G-T4 saved")
    
    gt5, planner_stage_counts = compute_table_GT5(data, raw_df)
    gt5.to_csv(OUTPUT_DIR / "tables" / "G_T5_Best_Configuration_Per_Instance.csv", index=False)
    render_table_image(gt5, OUTPUT_DIR / "tables" / "G_T5_Best_Configuration_Per_Instance.png",
                      "G-T5: Best Configuration Per Instance (Headline Result)")
    tables_dict["GT5"] = gt5
    print("  G-T5 saved")
    
    # G-G4 (uses planner_stage_counts)
    plot_G_G4(planner_stage_counts)
    print("  G-G4 saved")
    
    # Summary Dashboard
    plot_summary_dashboard(data)
    print("  Summary Dashboard saved")
    
    # Report
    generate_report(tables_dict)
    
    print("\n" + "=" * 70)
    print("SECTION 1 ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Tables: {OUTPUT_DIR / 'tables'}")
    print(f"Graphs: {OUTPUT_DIR / 'graphs'}")


if __name__ == "__main__":
    main()
