"""
Stage 2 (Architecture-Aware) Analysis Script - Visual Output Generator
====================================================================================
Reads Stage 2 data and produces:
  1. Formatted Markdown Summaries
  2. Tables as both Markdown and styled PNG images
  3. High-quality academic Graphs (PNGs)
  4. Architectural Diagrams (Mermaid rendered to PNGs)

Organized into: analysis/output/stage2/{1_Summary, 2_Tables, 3_Graphs, 4_Diagrams}
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import sys
import io
import os
import json
import base64
import requests
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Paths & Setup ───────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "output" / "stage2"

DIR_SUMMARY = OUTPUT_DIR / "1_Summary"
DIR_TABLES = OUTPUT_DIR / "2_Tables"
DIR_GRAPHS = OUTPUT_DIR / "3_Graphs"
DIR_DIAGRAMS = OUTPUT_DIR / "4_Diagrams"

for d in [DIR_SUMMARY, DIR_TABLES, DIR_GRAPHS, DIR_DIAGRAMS]:
    d.mkdir(parents=True, exist_ok=True)

# Data files
PLANNER_EXEC_CSV = REPO_ROOT / "results" / "planner_execution_data.csv"
ARCH_AWARE_PLANNER_CSV = REPO_ROOT / "results" / "arch_aware" / "arch_aware_planner_execution_data.csv"
CROSS_TEST_CSV = REPO_ROOT / "results" / "cross_test" / "cross_test_planner_execution_data.csv"
LLM_GEN_CSV = REPO_ROOT / "results" / "arch_aware" / "LLM Results" / "arch_aware_llm_generation_data.csv"
DIFF_METRICS_CSV = REPO_ROOT / "validation_and_evaluation" / "data" / "production" / "arch_aware" / "arch_aware_pddl_diff_metrics.csv"
IMPROVEMENT_CSV = REPO_ROOT / "results" / "arch_aware" / "improvement" / "improvement_results.csv"

# Set academic theme for all graphs
sns.set_theme(style="ticks", context="paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['font.family'] = 'serif'

# ── Constants ──────────────────────────────────────────────────────────
PLANNERS = ["lama", "decstar", "bfws", "madagascar"]
DOMAINS = ["visitall", "snake", "ricochet-robots", "depots", "barman"]
PROMPT_MAP = {1: "lama", 2: "decstar", 3: "bfws", 4: "madagascar"}
TARGET_MAP = {"lama": 1, "decstar": 2, "bfws": 3, "madagascar": 4}

LLM_SHORT_NAMES = {
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "deepseek-reasoner": "DeepSeek-R1",
    "claude-opus-4-6": "Claude 4.6",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1",
}

NUMERIC_COLS = ["PlanCost", "Runtime_internal_s", "Runtime_wall_s"]
REORDER_COLS = ["req_reordered", "type_reordered", "pred_reordered", "func_reordered",
                "actions_reordered", "params_reordered", "pre_reordered",
                "eff_add_reordered", "eff_del_reordered"]
COMPONENT_LABELS = ["Requirements", "Types", "Predicates", "Functions",
                    "Actions", "Parameters", "Preconditions", "Add Effects", "Delete Effects"]

# ── Helper Functions ─────────────────────────────────────────────────────
def shorten_llm(name: str) -> str:
    if pd.isna(name): return name
    for k, v in LLM_SHORT_NAMES.items():
        if k in str(name): return v
    if "gpt" in str(name).lower(): return "GPT-5.4"
    if "deepseek" in str(name).lower(): return "DeepSeek-R1"
    if "claude" in str(name).lower(): return "Claude 4.6"
    if "gemini" in str(name).lower(): return "Gemini 3.1"
    return str(name)

def save_table_png(df: pd.DataFrame, filename: str, title: str):
    if len(df) > 35: return
    col_width = max(len(str(c)) for c in df.columns) * 0.15 + 1.0
    row_height = 0.5
    size = (len(df.columns) * col_width, (len(df) + 1.5) * row_height)
    
    fig, ax = plt.subplots(figsize=size)
    ax.axis('off')
    plt.title(title, fontsize=12, pad=10, weight='bold', fontname='serif')
    
    mpl_table = ax.table(cellText=df.values, bbox=[0, 0, 1, 1], colLabels=df.columns, cellLoc='center')
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(9)
    for k, cell in mpl_table._cells.items():
        cell.set_edgecolor('lightgray')
        if k[0] == 0:
            cell.set_text_props(weight='bold', color='white', fontname='serif')
            cell.set_facecolor('#4c72b0')
        else:
            cell.set_facecolor('#f9f9f9' if k[0] % 2 == 0 else 'white')
            cell.set_text_props(fontname='serif')
    plt.tight_layout()
    plt.savefig(DIR_TABLES / f"{filename}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

def save_md_table(df: pd.DataFrame, filename: str, title: str):
    path = DIR_TABLES / f"{filename}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n")
    save_table_png(df, filename, title)

def save_mermaid_png(mermaid_str: str, filename: str):
    clean_str = mermaid_str.strip().replace("```mermaid", "").replace("```", "").strip()
    try:
        b64 = base64.b64encode(clean_str.encode('utf-8')).decode('ascii')
        url = f"https://mermaid.ink/img/{b64}"
        resp = requests.get(url)
        resp.raise_for_status()
        with open(DIR_DIAGRAMS / f"{filename}.png", 'wb') as f:
            f.write(resp.content)
    except Exception as e:
        print(f"Failed to generate {filename}.png: {e}")

# ── Data Loading ─────────────────────────────────────────────────────────
def load_data():
    base_df = pd.read_csv(PLANNER_EXEC_CSV)
    base_df = base_df[base_df["Stage"].str.strip().str.upper() == "BASELINE"].copy()
    
    arch_df = pd.read_csv(ARCH_AWARE_PLANNER_CSV) if ARCH_AWARE_PLANNER_CSV.exists() else pd.DataFrame()
    cross_df = pd.read_csv(CROSS_TEST_CSV) if CROSS_TEST_CSV.exists() else pd.DataFrame()
    llm_df = pd.read_csv(LLM_GEN_CSV) if LLM_GEN_CSV.exists() else pd.DataFrame()
    diff_df = pd.read_csv(DIFF_METRICS_CSV) if DIFF_METRICS_CSV.exists() else pd.DataFrame()
    imp_df = pd.read_csv(IMPROVEMENT_CSV) if IMPROVEMENT_CSV.exists() else pd.DataFrame()
    
    for df in [base_df, arch_df, cross_df]:
        if df.empty: continue
        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return base_df, arch_df, cross_df, llm_df, diff_df, imp_df

# ─────────────────────────────────────────────────────────────────────
# Specialization Logic: IPC Cross-Test Calculation
# ─────────────────────────────────────────────────────────────────────
def compute_specialization_matrix(imp_df, base_df, arch_df, cross_df):
    results = []
    
    if imp_df.empty or base_df.empty or cross_df.empty:
        return pd.DataFrame()
        
    improved = imp_df[imp_df["IMPROVEMENT_DETECTED"] == True]
    
    for _, row in improved.iterrows():
        domain = row["Domain"]
        llm = row["LLM"]
        target = row["Target_Planner"].lower()
        prompt_id = TARGET_MAP.get(target)
        
        for actual in PLANNERS:
            b_sub = base_df[(base_df["Domain_Name"] == domain) & (base_df["Planner_Used"].str.lower() == actual)]
            b_times = b_sub.set_index("Problem_Instance")["Runtime_wall_s"]
            
            if actual == target:
                t_sub = arch_df[(arch_df["Domain_Name"] == domain) & (arch_df["LLM_Used"] == llm) & (arch_df["Planner_Used"].str.lower() == actual) & (arch_df["PromptID"] == prompt_id)]
            else:
                t_sub = cross_df[(cross_df["Domain_Name"] == domain) & (cross_df["LLM_Used"] == llm) & (cross_df["Planner_Used"].str.lower() == actual) & (cross_df["PromptID"] == prompt_id)]
                
            t_times = t_sub.set_index("Problem_Instance")["Runtime_wall_s"]
            
            gains = []
            # Calculate IPC Gain for each instance (1 to 15)
            for i in range(1, 16):
                inst = f"instance-{i:02d}.pddl"
                b = b_times.get(inst, np.inf)
                t = t_times.get(inst, np.inf)
                if isinstance(b, pd.Series): b = b.iloc[0]
                if isinstance(t, pd.Series): t = t.iloc[0]
                if pd.isna(b): b = np.inf
                if pd.isna(t): t = np.inf
                
                if b == np.inf and t == np.inf:
                    gains.append(0.0) # Correct IPC math: append 0 to divide by full 15 instances
                    continue
                
                t_star = min(b, t)
                base_ipc = t_star / b if b != np.inf else 0.0
                test_ipc = t_star / t if t != np.inf else 0.0
                gains.append(test_ipc - base_ipc)
                
            mean_gain = np.mean(gains) if gains else 0.0
            results.append({
                "Target_Planner": target,
                "Actual_Planner": actual,
                "Domain": domain,
                "LLM": llm,
                "Mean_IPC_Gain": mean_gain
            })
            
    return pd.DataFrame(results)

# ─────────────────────────────────────────────────────────────────────
# 1. Summaries
# ─────────────────────────────────────────────────────────────────────
def generate_summary(llm_df, arch_df, imp_df):
    content = "# S2.1 & S2.3 — Stage 2 Summary\n\n"
    
    if not llm_df.empty:
        api_time = pd.to_numeric(llm_df.get("LLM API Time S"), errors="coerce")
        content += f"## LLM API Summary\n"
        content += f"- **Total Calls:** {len(llm_df)}\n"
        content += f"- **Mean API Time:** {api_time.mean():.2f} s\n"
        in_tok = pd.to_numeric(llm_df.get("Input Tokens Consumed"), errors="coerce").sum()
        out_tok = pd.to_numeric(llm_df.get("Output Tokens Generated"), errors="coerce").sum()
        content += f"- **Total Tokens:** {(in_tok + out_tok):,.0f}\n\n"
        
    if not arch_df.empty:
        success = arch_df[arch_df["Output_Status"] == "SUCCESS"]
        content += f"## Planner Execution Summary (Target Only)\n"
        content += f"- **Total Runs:** {len(arch_df)}\n"
        content += f"- **Overall Solve Rate:** {(len(success)/len(arch_df)*100):.2f}% ({len(success)}/{len(arch_df)})\n\n"
        
    if not imp_df.empty:
        improved = imp_df[imp_df["IMPROVEMENT_DETECTED"] == True]
        content += f"## Improvement Detection Summary\n"
        content += f"- **Total Triples Tested:** {len(imp_df)}\n"
        content += f"- **Improved Triples:** {len(improved)}\n"
        content += f"- **Improvement Rate:** {(len(improved)/len(imp_df)*100):.2f}%\n"

    with open(DIR_SUMMARY / "S2_1_Summary.md", "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────
# 2. Tables
# ─────────────────────────────────────────────────────────────────────
def generate_tables(base_df, arch_df, cross_df, llm_df, diff_df, imp_df):
    llm_df["Short_LLM"] = llm_df["LLM Model"].apply(shorten_llm)
    
    # S2-T1: LLM API Performance
    rows1 = []
    for llm in llm_df["Short_LLM"].unique():
        sub = llm_df[llm_df["Short_LLM"] == llm]
        errs = sub[sub["LLM_Status"].str.lower() != "passed"]
        tl_errs = errs[errs["LLM_Status"].str.contains("token_limit", case=False, na=False)]
        
        in_tok = pd.to_numeric(sub["Input Tokens Consumed"], errors="coerce").sum()
        out_tok = pd.to_numeric(sub["Output Tokens Generated"], errors="coerce").sum()
        time = pd.to_numeric(sub["LLM API Time S"], errors="coerce").mean()
        
        rows1.append({
            "LLM Model": llm,
            "API Calls": len(sub),
            "Successful": len(sub) - len(errs),
            "Token Limit Errors": len(tl_errs),
            "Other Errors": len(errs) - len(tl_errs),
            "Input Tokens (Total)": f"{in_tok:,.0f}",
            "Output Tokens (Total)": f"{out_tok:,.0f}",
            "Total Tokens": f"{(in_tok + out_tok):,.0f}",
            "Mean API Time (s)": f"{time:.1f}"
        })
    save_md_table(pd.DataFrame(rows1), "S2_T1_LLM_Performance", "S2-T1: LLM API Performance")

    # S2-T2: Token Limit Failure Details
    tl_df = llm_df[llm_df["LLM_Status"].str.contains("token_limit", case=False, na=False)]
    if not tl_df.empty:
        rows2 = []
        for _, r in tl_df.iterrows():
            rows2.append({
                "Domain": str(r.get("Domain Name")).capitalize(),
                "LLM": shorten_llm(r.get("LLM Model")),
                "Target Planner": PROMPT_MAP.get(int(r.get("Prompt ID", 0)), "Unknown").upper(),
                "Prompt ID": r.get("Prompt ID"),
                "Error Type": "Token Limit Reached"
            })
        save_md_table(pd.DataFrame(rows2), "S2_T2_Token_Limit_Failures", "S2-T2: Token Limit Failure Details")

    # S2-T5: Detailed Failure Analysis
    v4_fails = llm_df[llm_df["Validation Status"].str.upper() == "INVALID"]
    rows5 = []
    if not tl_df.empty:
        for _, r in tl_df.iterrows():
            rows5.append({"Domain": str(r.get("Domain Name")).capitalize(), "LLM": shorten_llm(r.get("LLM Model")), "Planner Prompt": PROMPT_MAP.get(int(r.get("Prompt ID", 0)), "Unknown").upper(), "Failed Stage": "API", "Failure Details": "Token Limit"})
    if not v4_fails.empty:
        for _, r in v4_fails.iterrows():
            rows5.append({"Domain": str(r.get("Domain Name")).capitalize(), "LLM": shorten_llm(r.get("LLM Model")), "Planner Prompt": PROMPT_MAP.get(int(r.get("Prompt ID", 0)), "Unknown").upper(), "Failed Stage": "V4 Semantic", "Failure Details": "Invalid logic change"})
    if rows5:
        save_md_table(pd.DataFrame(rows5), "S2_T5_Detailed_Failures", "S2-T5: Detailed Failure Analysis")

    # S2-T3: Token Usage by LLM x Planner Prompt
    pivot_tok = llm_df.pivot_table(index="Short_LLM", columns="Prompt ID", values="Output Tokens Generated", aggfunc="mean")
    rows3 = []
    for llm in llm_df["Short_LLM"].unique():
        row = {"LLM": llm}
        for pid in [1, 2, 3, 4]:
            val = pivot_tok.loc[llm, pid] if llm in pivot_tok.index and pid in pivot_tok.columns else np.nan
            row[f"{PROMPT_MAP[pid].upper()} Prompt"] = f"{val:,.0f}" if pd.notna(val) else "—"
        rows3.append(row)
    save_md_table(pd.DataFrame(rows3), "S2_T3_Tokens_By_Prompt", "S2-T3: Output Token Usage by LLM × Planner Prompt")

    # S2-T4: Validation Summary
    valid = len(llm_df[llm_df["Validation Status"].str.lower() == "valid"])
    invalid = len(llm_df[llm_df["Validation Status"].str.lower() == "invalid"])
    rejected = len(llm_df[llm_df["Validation Status"].str.lower() == "rejected"])
    save_md_table(pd.DataFrame([
        {"Status": "VALID", "Count": valid, "Percentage": f"{valid/len(llm_df)*100:.1f}%"},
        {"Status": "INVALID (V4 Semantic)", "Count": invalid, "Percentage": f"{invalid/len(llm_df)*100:.1f}%"},
        {"Status": "REJECTED (V1/2/3)", "Count": rejected, "Percentage": f"{rejected/len(llm_df)*100:.1f}%"}
    ]), "S2_T4_Validation_Summary", "S2-T4: Validation Outcome Summary")

    # S2-T6: Validated Domain Distribution
    valid_llm = llm_df[llm_df["Validation Status"].str.upper() == "VALID"]
    rows6 = []
    for d in DOMAINS:
        row = {"Domain": d.capitalize()}
        total_v = 0
        for pid in [1, 2, 3, 4]:
            v_cnt = len(valid_llm[(valid_llm["Domain Name"] == d) & (valid_llm["Prompt ID"] == pid)])
            row[f"{PROMPT_MAP[pid].upper()}"] = f"{v_cnt}/4"
            total_v += v_cnt
        row["Total"] = f"{total_v}/16"
        rows6.append(row)
    save_md_table(pd.DataFrame(rows6), "S2_T6_Valid_Domains", "S2-T6: Validated Domain Distribution")

    # S2-T7: Reordering by Prompt
    if not diff_df.empty and not llm_df.empty:
        valid_diff = diff_df[diff_df["validation_status"].str.lower() == "valid"].copy()
        merged_diff = valid_diff.merge(llm_df[["ID", "Prompt ID"]], left_on="LLM_ID", right_on="ID", how="left")
        rows7 = []
        for col, label in zip(REORDER_COLS, COMPONENT_LABELS):
            if col not in merged_diff.columns: continue
            row = {"PDDL Component": label}
            for pid in [1, 2, 3, 4]:
                sub = merged_diff[merged_diff["Prompt ID"] == pid]
                tot = len(sub)
                cnt = pd.to_numeric(sub[col], errors="coerce").sum()
                row[f"{PROMPT_MAP[pid].upper()} prompt"] = f"{int(cnt)}/{tot}" if tot > 0 else "0/0"
            rows7.append(row)
        save_md_table(pd.DataFrame(rows7), "S2_T7_Reordering_By_Prompt", "S2-T7: Reordering Patterns by Target Prompt")

    # S2-T8: Target Planner Summary
    rows8 = []
    for p in PLANNERS:
        sub = arch_df[arch_df["Planner_Used"].str.lower() == p]
        suc = sub[sub["Output_Status"] == "SUCCESS"]
        if len(sub) > 0:
            rows8.append({
                "Target Planner": p.upper(),
                "Total Runs": len(sub),
                "SUCCESS": len(suc),
                "TIMEOUT": len(sub[sub["Output_Status"] == "TIMEOUT"]),
                "Solve Rate (%)": f"{(len(suc)/len(sub)*100):.1f}%"
            })
    save_md_table(pd.DataFrame(rows8), "S2_T8_Planner_Summary", "S2-T8: Target Planner Execution Summary")

    # S2-T9: Coverage by Domain x Target Planner
    rows9 = []
    for d in DOMAINS:
        row = {"Domain": d.capitalize()}
        for p in PLANNERS:
            sub = arch_df[(arch_df["Domain_Name"] == d) & (arch_df["Planner_Used"].str.lower() == p)]
            llms_for_p = sub["LLM_Used"].unique()
            if len(llms_for_p) > 0:
                covs = []
                for llm in llms_for_p:
                    covs.append(len(sub[(sub["LLM_Used"] == llm) & (sub["Output_Status"] == "SUCCESS")]))
                row[f"{p.upper()} Avg Coverage"] = f"{np.mean(covs):.1f}/15"
            else:
                row[f"{p.upper()} Avg Coverage"] = "0.0/15"
        rows9.append(row)
    save_md_table(pd.DataFrame(rows9), "S2_T9_Coverage_By_Domain", "S2-T9: Coverage by Domain × Target Planner")

    # S2-T10: Improvement Detection Summary
    if not imp_df.empty:
        imp_df["Short_LLM"] = imp_df["LLM"].apply(shorten_llm)
        improved = len(imp_df[imp_df["IMPROVEMENT_DETECTED"] == True])
        not_imp = len(imp_df[imp_df["IMPROVEMENT_DETECTED"] == False])
        save_md_table(pd.DataFrame([
            {"Metric": "Total triples tested", "Value": len(imp_df)},
            {"Metric": "IMPROVEMENT_DETECTED = True", "Value": improved},
            {"Metric": "IMPROVEMENT_DETECTED = False", "Value": not_imp},
            {"Metric": "Improvement rate (%)", "Value": f"{(improved/len(imp_df)*100):.1f}%"}
        ]), "S2_T10_Improvement_Summary", "S2-T10: Improvement Detection Summary")

        # S2-T14: Failed Condition Analysis
        failed = imp_df[imp_df["IMPROVEMENT_DETECTED"] == False]
        if not failed.empty:
            c_stat = len(failed)
            c_prac = len(failed[failed['Mean_IPC_Gain'] <= 0])
            c_zero = len(failed[(failed['Coverage_Stage0'] == 0) & (failed['Coverage_Stage2'] == 0)])
            c_cov = len(failed[failed['Delta_Coverage'] < 0])
            
            fail_rows = [
                {"Failed Condition Pattern": "Failed Statistical Significance (p > 0.25)", "Count": c_stat, "Description": "Positive or negative gains, but not statistically significant."},
                {"Failed Condition Pattern": "Failed Practical Significance (Mean IPC Gain <= 0)", "Count": c_prac, "Description": "The modified domain performed worse, timed out, or had no gain."},
                {"Failed Condition Pattern": "Zero Coverage (Baseline & Target)", "Count": c_zero, "Description": "Planner timed out on all instances for both baseline and modified."},
                {"Failed Condition Pattern": "Failed Coverage Preservation (Target Cov < Base Cov)", "Count": c_cov, "Description": "The modified domain solved fewer instances than the baseline."}
            ]
            save_md_table(pd.DataFrame(fail_rows), "S2_T14_Failed_Conditions", "S2-T14: Failed Condition Analysis (Out of 33 Triples)")

        # S2-T16: Statistical Significance Distribution
        improved_df = imp_df[imp_df["IMPROVEMENT_DETECTED"] == True]
        if not imp_df.empty:
            p_vals = imp_df["Wilcoxon_P_Value"].dropna()
            bins = [0, 0.001, 0.01, 0.05, 0.10, 0.25, 1.0]
            labels = ["p <= 0.001", "0.001 < p <= 0.01", "0.01 < p <= 0.05", "0.05 < p <= 0.10", "0.10 < p <= 0.25", "p > 0.25"]
            counts = pd.cut(p_vals, bins=bins, labels=labels, include_lowest=True).value_counts(sort=False)
            save_md_table(counts.reset_index(name="Count"), "S2_T16_P_Value_Distribution", "S2-T16: Statistical Significance Distribution")

        # S2-T17: Top 10 Best IPC Gains
        if not improved_df.empty:
            top10 = improved_df.nlargest(10, "Mean_IPC_Gain")[["Domain", "Short_LLM", "Target_Planner", "Mean_IPC_Gain"]].copy()
            top10.insert(0, "Rank", range(1, len(top10)+1))
            top10["Mean_IPC_Gain"] = top10["Mean_IPC_Gain"].round(3)
            save_md_table(top10, "S2_T17_Top_10_Gains", "S2-T17: Top 10 Best IPC Gains")

        # S2-T18: Top 10 Worst Performers
        if not failed.empty:
            worst10 = failed.nsmallest(10, "Mean_IPC_Gain")[["Domain", "Short_LLM", "Target_Planner", "Mean_IPC_Gain", "Failed_Condition"]].copy()
            worst10.insert(0, "Rank", range(1, len(worst10)+1))
            worst10["Mean_IPC_Gain"] = worst10["Mean_IPC_Gain"].round(3)
            save_md_table(worst10, "S2_T18_Worst_10_Performers", "S2-T18: Top 10 Worst Performers")

        # Domain
        rows11 = []
        for d in DOMAINS:
            sub = imp_df[imp_df["Domain"] == d]
            if len(sub) == 0: continue
            imp = sub[sub["IMPROVEMENT_DETECTED"] == True]
            rows11.append({
                "Domain": d.capitalize(),
                "Triples Tested": len(sub),
                "Improved": len(imp),
                "Rate (%)": f"{(len(imp)/len(sub)*100):.1f}%",
                "Avg Mean IPC Gain": f"{imp['Mean_IPC_Gain'].mean():.3f}" if len(imp)>0 else "—",
                "Best Single Gain": f"{imp['Mean_IPC_Gain'].max():.3f}" if len(imp)>0 else "—"
            })
        save_md_table(pd.DataFrame(rows11).sort_values("Improved", ascending=False), "S2_T11_Improvement_By_Domain", "S2-T11: Improvement by Domain")

        # Planner
        rows12 = []
        for p in PLANNERS:
            sub = imp_df[imp_df["Target_Planner"].str.lower() == p]
            if len(sub) == 0: continue
            imp = sub[sub["IMPROVEMENT_DETECTED"] == True]
            rows12.append({
                "Target Planner": p.upper(),
                "Triples Tested": len(sub),
                "Improved": len(imp),
                "Rate (%)": f"{(len(imp)/len(sub)*100):.1f}%"
            })
        save_md_table(pd.DataFrame(rows12).sort_values("Improved", ascending=False), "S2_T12_Improvement_By_Planner", "S2-T12: Improvement by Target Planner")

        # LLM
        rows13 = []
        for llm in imp_df["Short_LLM"].unique():
            sub = imp_df[imp_df["Short_LLM"] == llm]
            imp = sub[sub["IMPROVEMENT_DETECTED"] == True]
            rows13.append({
                "LLM": llm,
                "Triples Tested": len(sub),
                "Improved": len(imp),
                "Rate (%)": f"{(len(imp)/len(sub)*100):.1f}%"
            })
        save_md_table(pd.DataFrame(rows13).sort_values("Improved", ascending=False), "S2_T13_Improvement_By_LLM", "S2-T13: Improvement by LLM")

        # S2-T15: Complete Improved Configs
        improved = imp_df[imp_df["IMPROVEMENT_DETECTED"] == True].sort_values("Mean_IPC_Gain", ascending=False)
        cols15 = ["Domain", "Short_LLM", "Target_Planner", "Mean_IPC_Gain", "Wilcoxon_P_Value", "Coverage_Stage0", "Coverage_Stage2", "Delta_Coverage"]
        t15 = improved[cols15].copy()
        t15.columns = ["Domain", "LLM", "Target Planner", "Mean IPC Gain", "p-value", "Base Cov", "S2 Cov", "Delta Cov"]
        t15["Mean IPC Gain"] = t15["Mean IPC Gain"].round(3)
        t15["p-value"] = t15["p-value"].round(3)
        save_md_table(t15, "S2_T15_All_Improved", "S2-T15: Complete Improved Configurations")

    # S2-T19: Cross-Test Execution Summary
    if not cross_df.empty:
        rows19 = []
        for p in PLANNERS:
            sub = cross_df[cross_df["Planner_Used"].str.lower() == p]
            if len(sub) == 0: continue
            suc = sub[sub["Output_Status"] == "SUCCESS"]
            rows19.append({
                "Planner (as non-target)": p.upper(),
                "Total Runs": len(sub),
                "SUCCESS": len(suc),
                "TIMEOUT": len(sub[sub["Output_Status"] == "TIMEOUT"]),
                "Solve Rate (%)": f"{(len(suc)/len(sub)*100):.1f}%"
            })
        save_md_table(pd.DataFrame(rows19), "S2_T19_Cross_Test_Summary", "S2-T19: Cross-Test Execution Summary")

        # S2-T20: Cross-Test Success Rate by Domain
        rows20 = []
        for d in DOMAINS:
            sub = cross_df[cross_df["Domain_Name"] == d]
            if len(sub) == 0: continue
            suc = sub[sub["Output_Status"] == "SUCCESS"]
            rows20.append({
                "Domain": d.capitalize(),
                "Total Cross-Test Runs": len(sub),
                "SUCCESS": len(suc),
                "Solve Rate": f"{(len(suc)/len(sub)*100):.1f}%"
            })
        save_md_table(pd.DataFrame(rows20), "S2_T20_Cross_Test_By_Domain", "S2-T20: Cross-Test Success Rate by Domain")

    # S2-T21: Cross-Test IPC Specialization Matrix
    spec_df = compute_specialization_matrix(imp_df, base_df, arch_df, cross_df)
    if not spec_df.empty:
        pivot_spec = spec_df.groupby(["Target_Planner", "Actual_Planner"])["Mean_IPC_Gain"].mean().unstack()
        valid_cols = [p for p in PLANNERS if p in pivot_spec.columns]
        valid_rows = [p for p in PLANNERS if p in pivot_spec.index]
        pivot_spec = pivot_spec.loc[valid_rows, valid_cols]
        
        matrix21 = pivot_spec.copy()
        matrix21.index = [f"{p.upper()} Prompt" for p in matrix21.index]
        matrix21.columns = [f"{p.upper()} (Actual)" for p in matrix21.columns]
        matrix21 = matrix21.round(3).reset_index()
        matrix21.rename(columns={"index": "Target Planner"}, inplace=True)
        save_md_table(matrix21, "S2_T21_IPC_Specialization", "S2-T21: Cross-Test IPC Specialization Matrix")

    # S2-T22 through T25: Specialization Verdict Analysis
    if spec_df is not None and not spec_df.empty:
        spec_pivot = spec_df.groupby(["Domain", "LLM", "Target_Planner", "Actual_Planner"])["Mean_IPC_Gain"].mean().reset_index()
        
        verdicts = []
        for (d, l, t), group in spec_pivot.groupby(["Domain", "LLM", "Target_Planner"]):
            t_gain_arr = group[group["Actual_Planner"] == t]["Mean_IPC_Gain"].values
            if len(t_gain_arr) == 0: continue
            t_gain = t_gain_arr[0]
            
            nt_gains = group[group["Actual_Planner"] != t]["Mean_IPC_Gain"].values
            nt_avg = np.mean(nt_gains) if len(nt_gains) > 0 else 0
            spec_index = t_gain - nt_avg
            
            if nt_avg <= -0.005:
                quadrant = "Specialized"
            elif nt_avg > t_gain:
                quadrant = "Anti-Specialized"
            elif abs(nt_avg) <= 0.005:
                quadrant = "Neutral"
            else:
                quadrant = "Universally Better"
            
            verdicts.append({
                "Domain": d.capitalize(),
                "LLM": shorten_llm(l),
                "Target Planner": t.upper(),
                "Target Gain": round(t_gain, 4),
                "Avg Non-Target Gain": round(nt_avg, 4),
                "Specialization Index": round(spec_index, 4),
                "Verdict": quadrant
            })
        
        verdict_df = pd.DataFrame(verdicts)
        
        if not verdict_df.empty:
            # S2-T22: Full verdict table
            save_md_table(verdict_df.sort_values("Specialization Index", ascending=False), 
                         "S2_T22_Specialization_Verdicts", "S2-T22: Specialization Verdict per Configuration")
            
            # S2-T23: By Planner
            rows23 = []
            for p in PLANNERS:
                sub = verdict_df[verdict_df["Target Planner"] == p.upper()]
                if len(sub) == 0: continue
                rows23.append({
                    "Target Planner": p.upper(),
                    "Total": len(sub),
                    "Specialized": len(sub[sub["Verdict"] == "Specialized"]),
                    "Universally Better": len(sub[sub["Verdict"] == "Universally Better"]),
                    "Anti-Specialized": len(sub[sub["Verdict"] == "Anti-Specialized"]),
                    "Neutral": len(sub[sub["Verdict"] == "Neutral"]),
                    "Mean Spec Index": f"{sub['Specialization Index'].mean():.4f}"
                })
            save_md_table(pd.DataFrame(rows23), "S2_T23_Specialization_By_Planner", "S2-T23: Specialization Verdict by Planner")
            
            # S2-T24: By LLM
            rows24 = []
            for llm_short in verdict_df["LLM"].unique():
                sub = verdict_df[verdict_df["LLM"] == llm_short]
                rows24.append({
                    "LLM": llm_short,
                    "Total": len(sub),
                    "Specialized": len(sub[sub["Verdict"] == "Specialized"]),
                    "Universally Better": len(sub[sub["Verdict"] == "Universally Better"]),
                    "Anti-Specialized": len(sub[sub["Verdict"] == "Anti-Specialized"]),
                    "Neutral": len(sub[sub["Verdict"] == "Neutral"]),
                    "Mean Spec Index": f"{sub['Specialization Index'].mean():.4f}"
                })
            save_md_table(pd.DataFrame(rows24), "S2_T24_Specialization_By_LLM", "S2-T24: Specialization Verdict by LLM")
            
            # S2-T25: High-level summary
            spec_count = len(verdict_df[verdict_df["Verdict"] == "Specialized"])
            univ_count = len(verdict_df[verdict_df["Verdict"] == "Universally Better"])
            anti_count = len(verdict_df[verdict_df["Verdict"] == "Anti-Specialized"])
            neut_count = len(verdict_df[verdict_df["Verdict"] == "Neutral"])
            tgt_gt_nt = len(verdict_df[verdict_df["Specialization Index"] > 0])
            neg_nt = len(verdict_df[verdict_df["Avg Non-Target Gain"] < 0])
            
            save_md_table(pd.DataFrame([
                {"Metric": "Total configs analyzed", "Value": len(verdict_df)},
                {"Metric": "Specialized (target up, non-target down)", "Value": f"{spec_count} ({spec_count/len(verdict_df)*100:.1f}%)"},
                {"Metric": "Universally Better (all planners up)", "Value": f"{univ_count} ({univ_count/len(verdict_df)*100:.1f}%)"},
                {"Metric": "Anti-Specialized (non-target > target)", "Value": f"{anti_count} ({anti_count/len(verdict_df)*100:.1f}%)"},
                {"Metric": "Neutral (non-target ≈ 0)", "Value": f"{neut_count} ({neut_count/len(verdict_df)*100:.1f}%)"},
                {"Metric": "Configs where Target Gain > Avg Non-Target", "Value": f"{tgt_gt_nt}/{len(verdict_df)}"},
                {"Metric": "Configs with negative non-target gains", "Value": f"{neg_nt}/{len(verdict_df)}"},
                {"Metric": "Mean Specialization Index", "Value": f"{verdict_df['Specialization Index'].mean():.4f}"},
            ]), "S2_T25_Specialization_Summary", "S2-T25: Specialization Index Summary")

    return spec_df, verdict_df if 'verdict_df' in dir() else pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────
# 3. Graphs
# ─────────────────────────────────────────────────────────────────────
def generate_graphs(arch_df, llm_df, imp_df, spec_df, verdict_df):
    llm_df["Short_LLM"] = llm_df["LLM Model"].apply(shorten_llm)
    imp_df["Short_LLM"] = imp_df["LLM"].apply(shorten_llm)

    # S2-G12: Validation Outcome by LLM (Fixed logic)
    plt.figure(figsize=(8, 5))
    llm_df_copy = llm_df.copy()
    llm_df_copy.loc[llm_df_copy["LLM_Status"].str.contains("token_limit", case=False, na=False), "Validation Status"] = "TOKEN LIMIT"
    val_counts = llm_df_copy.groupby(["Short_LLM", "Validation Status"]).size().unstack(fill_value=0)
    
    colors = []
    for c in val_counts.columns:
        if c.upper() == "VALID": colors.append("#55a868")
        elif c.upper() == "INVALID": colors.append("#c44e52")
        elif c.upper() == "REJECTED": colors.append("#ccb974")
        else: colors.append("#8c8c8c")
        
    val_counts.plot(kind="bar", stacked=True, color=colors, ax=plt.gca())
    from matplotlib.ticker import MaxNLocator
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.title("Validation Outcome by LLM", weight='bold')
    plt.xlabel("LLM", weight='bold')
    plt.ylabel("Files", weight='bold')
    plt.xticks(rotation=0)
    sns.despine()
    plt.legend(title="Status", bbox_to_anchor=(1.05, 1))
    plt.savefig(DIR_GRAPHS / "S2_G12_Validation_Stacked.png")
    plt.close()

    if not imp_df.empty:
        # S2-G1: Improvement Rate by Domain
        plt.figure(figsize=(7, 5))
        d_rates = imp_df.groupby("Domain")["IMPROVEMENT_DETECTED"].mean() * 100
        d_rates_df = d_rates.reset_index(name="Rate").sort_values("Rate", ascending=False)
        d_rates_df["Domain"] = d_rates_df["Domain"].str.capitalize()
        ax = sns.barplot(x="Domain", y="Rate", data=d_rates_df, color="#4c72b0")
        for i, v in enumerate(d_rates_df["Rate"]): ax.text(i, v + 1, f"{v:.1f}%", ha='center', weight='bold')
        plt.title("Improvement Rate by Domain", weight='bold')
        plt.ylim(0, 105)
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G1_Improvement_By_Domain.png")
        plt.close()

        # S2-G2: Improvement Rate by Planner
        plt.figure(figsize=(7, 5))
        rates = imp_df.groupby("Target_Planner")["IMPROVEMENT_DETECTED"].mean() * 100
        rates_df = rates.reset_index(name="Improvement Rate (%)").sort_values("Improvement Rate (%)", ascending=False)
        rates_df["Target_Planner"] = rates_df["Target_Planner"].str.upper()
        ax = sns.barplot(x="Target_Planner", y="Improvement Rate (%)", data=rates_df, palette="muted", legend=False, hue="Target_Planner")
        for i, v in enumerate(rates_df["Improvement Rate (%)"]): ax.text(i, v + 1, f"{v:.1f}%", ha='center', weight='bold')
        plt.title("Improvement Rate by Target Planner", weight='bold')
        plt.ylim(0, 105)
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G2_Improvement_By_Planner.png")
        plt.close()

        # S2-G3: Improvement Rate by LLM
        plt.figure(figsize=(7, 5))
        l_rates = imp_df.groupby("Short_LLM")["IMPROVEMENT_DETECTED"].mean() * 100
        l_rates_df = l_rates.reset_index(name="Rate").sort_values("Rate", ascending=False)
        ax = sns.barplot(x="Short_LLM", y="Rate", data=l_rates_df, color="#dd8452")
        for i, v in enumerate(l_rates_df["Rate"]): ax.text(i, v + 1, f"{v:.1f}%", ha='center', weight='bold')
        plt.title("Improvement Rate by LLM", weight='bold')
        plt.ylim(0, 105)
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G3_Improvement_By_LLM.png")
        plt.close()

        # S2-G4: Heatmap IPC Gain Domain x LLM
        for p in PLANNERS:
            sub = imp_df[imp_df["Target_Planner"].str.lower() == p]
            if sub.empty: continue
            pivot = sub.pivot_table(index="Domain", columns="Short_LLM", values="Mean_IPC_Gain")
            valid_d = [d for d in DOMAINS if d in pivot.index]
            pivot = pivot.loc[valid_d]
            pivot.index = [d.capitalize() for d in pivot.index]
            plt.figure(figsize=(6, 4))
            sns.heatmap(pivot, annot=True, cmap="RdYlGn", center=0, fmt=".3f", cbar_kws={'label': 'Mean IPC Gain'}, annot_kws={"size": 8})
            plt.xticks(rotation=45, ha='right')
            plt.title(f"Mean IPC Gain ({p.upper()} Target)", weight='bold')
            plt.tight_layout()
            plt.savefig(DIR_GRAPHS / f"S2_G4_Heatmap_IPC_{p.upper()}.png")
            plt.close()

        # S2-G5: Bar Chart Failed Conditions
        failed_sub = imp_df[imp_df["IMPROVEMENT_DETECTED"] == False]
        if not failed_sub.empty:
            c_stat = len(failed_sub)
            c_prac = len(failed_sub[failed_sub['Mean_IPC_Gain'] <= 0])
            c_zero = len(failed_sub[(failed_sub['Coverage_Stage0'] == 0) & (failed_sub['Coverage_Stage2'] == 0)])
            c_cov = len(failed_sub[failed_sub['Delta_Coverage'] < 0])
            
            labels = ["Failed Stat Sig\n(p > 0.25)", "Failed Prac Sig\n(Gain <= 0)", "Zero Coverage\n(Base & Target)", "Loss of Coverage"]
            sizes = [c_stat, c_prac, c_zero, c_cov]
            
            plt.figure(figsize=(8, 4))
            sns.barplot(x=sizes, y=labels, color="#c44e52")
            for i, v in enumerate(sizes):
                plt.text(v + 0.5, i, str(v), color='black', va='center', weight='bold')
                
            plt.title("Failure Condition Frequencies (Overlapping, Total=33)", weight='bold')
            plt.xlabel("Count", weight='bold')
            plt.xlim(0, 36)
            sns.despine()
            plt.tight_layout()
            plt.savefig(DIR_GRAPHS / "S2_G5_Failed_Conditions_Bar.png")
            plt.close()

        # S2-G6: IPC Gains Histogram (Fixed binning to isolate exactly 0)
        plt.figure(figsize=(8, 5))
        gains = imp_df["Mean_IPC_Gain"].dropna()
        
        max_abs = max(abs(gains.min()), abs(gains.max())) + 0.05
        bins = np.arange(-max_abs, max_abs, 0.01) - 0.005
        
        sns.histplot(gains, bins=bins, kde=False, color="#4c72b0", edgecolor='black')
        plt.axvline(0, color='red', linestyle='dashed', linewidth=2, label="Zero Gain")
        
        plt.title("Distribution of Mean IPC Gains (All Configs)", weight='bold')
        plt.xlabel("Mean IPC Gain vs Baseline", weight='bold')
        plt.ylabel("Count", weight='bold')
        plt.legend()
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G6_IPC_Gains_Hist.png")
        plt.close()

        # S2-G7: Box Plot IPC Gain by Planner
        plt.figure(figsize=(7, 5))
        sns.boxplot(x="Target_Planner", y="Mean_IPC_Gain", data=imp_df, palette="Set2", showfliers=False, whis=(0, 100))
        plt.axhline(0, color='red', linestyle='--')
        plt.title("IPC Gain Distribution by Planner", weight='bold')
        plt.xlabel("Target Planner", weight='bold')
        plt.ylabel("Mean IPC Gain", weight='bold')
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G7_BoxPlot_Planner.png")
        plt.close()

        # S2-G8: Box Plot IPC Gain by LLM
        plt.figure(figsize=(7, 5))
        sns.boxplot(x="Short_LLM", y="Mean_IPC_Gain", data=imp_df, palette="Set3", showfliers=False, whis=(0, 100))
        plt.axhline(0, color='red', linestyle='--')
        plt.title("IPC Gain Distribution by LLM", weight='bold')
        plt.xlabel("LLM", weight='bold')
        plt.ylabel("Mean IPC Gain", weight='bold')
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G8_BoxPlot_LLM.png")
        plt.close()

        # S2-G9: Box Plot IPC Gain by Domain
        plt.figure(figsize=(7, 5))
        sns.boxplot(x="Domain", y="Mean_IPC_Gain", data=imp_df, palette="Set1", showfliers=False, whis=(0, 100))
        plt.axhline(0, color='red', linestyle='--')
        plt.title("IPC Gain Distribution by Domain", weight='bold')
        plt.xlabel("Domain", weight='bold')
        plt.ylabel("Mean IPC Gain", weight='bold')
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S2_G9_BoxPlot_Domain.png")
        plt.close()

        # S2-G10: Volcano Plot (Clearer aesthetic)
        plt.figure(figsize=(9, 6))
        imp_df["neg_log_p"] = -np.log10(imp_df["Wilcoxon_P_Value"].replace(0, 1e-10))
        improved = imp_df[imp_df["IMPROVEMENT_DETECTED"] == True]
        not_improved = imp_df[imp_df["IMPROVEMENT_DETECTED"] == False]
        plt.scatter(improved["Mean_IPC_Gain"], improved["neg_log_p"], color="#005b96", label="Improved (Sig. & Prac.)", alpha=0.9, edgecolors='black', s=80)
        plt.scatter(not_improved["Mean_IPC_Gain"], not_improved["neg_log_p"], color="#d9534f", label="Not Improved", alpha=0.7, edgecolors='black', s=50)
        plt.axhline(-np.log10(0.25), color='gray', linestyle='dashed', label='p=0.25 Threshold')
        plt.axvline(0, color='black', linestyle='solid')
        plt.title("Wilcoxon Significance vs. IPC Gain", weight='bold')
        plt.xlabel("Mean IPC Gain", weight='bold')
        plt.ylabel("-log10(p-value)", weight='bold')
        plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S2_G10_Volcano_Plot.png")
        plt.close()

    # S2-G13: Target vs Non-Target Scatter (The Specialization Graph)
    if spec_df is not None and not spec_df.empty:
        plt.figure(figsize=(9, 7))
        spec_pivot = spec_df.groupby(["Domain", "LLM", "Target_Planner", "Actual_Planner"])["Mean_IPC_Gain"].mean().reset_index()
        
        scatter_data = []
        for (d, l, t), group in spec_pivot.groupby(["Domain", "LLM", "Target_Planner"]):
            t_gain = group[group["Actual_Planner"] == t]["Mean_IPC_Gain"].values
            if len(t_gain) == 0: continue
            t_gain = t_gain[0]
            
            nt_gains = group[group["Actual_Planner"] != t]["Mean_IPC_Gain"].values
            nt_gain = np.mean(nt_gains) if len(nt_gains) > 0 else 0
            
            scatter_data.append({"Target_Planner": t.upper(), "Target_Gain": t_gain, "Non_Target_Gain": nt_gain})
            
        sc_df = pd.DataFrame(scatter_data)
        
        sns.scatterplot(data=sc_df, x="Target_Gain", y="Non_Target_Gain", hue="Target_Planner", s=100, alpha=0.8, palette="Set1", edgecolor='black')
        plt.axvline(0, color='black', linestyle='--')
        plt.axhline(0, color='black', linestyle='--')
        
        plt.text(sc_df['Target_Gain'].max()*0.8, sc_df['Non_Target_Gain'].max()*0.8, "Universally Better\n(Top-Right)", color='gray', ha='center', va='center', alpha=0.5, fontsize=10, weight='bold')
        plt.text(sc_df['Target_Gain'].max()*0.8, sc_df['Non_Target_Gain'].min()*0.8, "Highly Specialized\n(Bottom-Right)", color='green', ha='center', va='center', alpha=0.7, fontsize=12, weight='bold')
        
        plt.title("Architecture Specialization: Target vs Non-Target Gains", weight='bold', fontsize=14, pad=15)
        plt.xlabel("IPC Gain on Target Planner (Optimized for)", weight='bold')
        plt.ylabel("Avg IPC Gain on Non-Target Planners", weight='bold')
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S2_G13_Specialization_Scatter.png")
        plt.close()

    # S2-G14: Specialization Quadrant Stacked Bar by Planner
    if verdict_df is not None and not verdict_df.empty:
        plt.figure(figsize=(9, 5))
        quad_colors = {"Specialized": "#2166ac", "Neutral": "#d1d1d1", "Universally Better": "#4daf4a", "Anti-Specialized": "#e41a1c"}
        quad_order = ["Specialized", "Neutral", "Universally Better", "Anti-Specialized"]
        
        planner_quads = verdict_df.groupby(["Target Planner", "Verdict"]).size().unstack(fill_value=0)
        for q in quad_order:
            if q not in planner_quads.columns:
                planner_quads[q] = 0
        planner_quads = planner_quads[quad_order]
        
        planner_quads.plot(kind="bar", stacked=True, color=[quad_colors[q] for q in quad_order], ax=plt.gca(), edgecolor='black')
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
        plt.title("Specialization Verdict by Target Planner", weight='bold', fontsize=13)
        plt.xlabel("Target Planner", weight='bold')
        plt.ylabel("Number of Configurations", weight='bold')
        plt.xticks(rotation=0)
        plt.legend(title="Verdict", bbox_to_anchor=(1.05, 1))
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S2_G14_Specialization_Quadrants.png")
        plt.close()

        # S2-G15: Specialization Index Histogram
        plt.figure(figsize=(8, 5))
        si_vals = verdict_df["Specialization Index"]
        max_abs_si = max(abs(si_vals.min()), abs(si_vals.max())) + 0.02
        si_bins = np.arange(-max_abs_si, max_abs_si, 0.01) - 0.005
        
        sns.histplot(si_vals, bins=si_bins, kde=False, color="#4c72b0", edgecolor='black')
        plt.axvline(0, color='red', linestyle='dashed', linewidth=2, label="No Specialization")
        
        positive_pct = len(si_vals[si_vals > 0]) / len(si_vals) * 100
        plt.text(si_vals.max() * 0.6, plt.gca().get_ylim()[1] * 0.85, 
                f"{positive_pct:.0f}% have\npositive index", color='#2166ac', weight='bold', fontsize=11)
        
        plt.title("Specialization Index Distribution\n(Target Gain − Avg Non-Target Gain)", weight='bold')
        plt.xlabel("Specialization Index", weight='bold')
        plt.ylabel("Count", weight='bold')
        plt.legend()
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S2_G15_Specialization_Index_Hist.png")
        plt.close()

    # S2-G16: Cross-Test Heatmap
    if spec_df is not None and not spec_df.empty:
        pivot_heat = spec_df.groupby(["Target_Planner", "Actual_Planner"])["Mean_IPC_Gain"].mean().unstack()
        valid_cols = [p for p in PLANNERS if p in pivot_heat.columns]
        valid_rows = [p for p in PLANNERS if p in pivot_heat.index]
        pivot_heat = pivot_heat.loc[valid_rows, valid_cols]
        pivot_heat.index = [p.upper() + " Prompt" for p in pivot_heat.index]
        pivot_heat.columns = [p.upper() for p in pivot_heat.columns]
        
        plt.figure(figsize=(8, 6))
        ax = sns.heatmap(pivot_heat, annot=True, cmap="RdYlGn", center=0, fmt=".3f", 
                        cbar_kws={'label': 'Mean IPC Gain'}, annot_kws={"size": 12, "weight": "bold"},
                        linewidths=2, linecolor='white')
        
        # Highlight diagonal cells with thicker borders
        for i in range(min(len(valid_rows), len(valid_cols))):
            ax.add_patch(plt.Rectangle((i, i), 1, 1, fill=False, edgecolor='black', linewidth=4))
        
        plt.title("Cross-Test IPC Specialization Matrix\n(Diagonal = Target Planner Performance)", weight='bold', fontsize=13)
        plt.xlabel("Actual Planner Used", weight='bold')
        plt.ylabel("Prompt Optimized For", weight='bold')
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S2_G16_CrossTest_Heatmap.png")
        plt.close()

# ─────────────────────────────────────────────────────────────────────
# 4. Diagrams
# ─────────────────────────────────────────────────────────────────────
def generate_diagrams():
    d1 = """graph LR
    A[Phase A: Prompt Gen<br>80 Calls] --> B[Phase B: Validation<br>V1-V4]
    B -->|75 Pass| C[Phase C: Target Run<br>1125 Planner Runs]
    C --> D[Phase D: Improvement<br>Detection]
    D -->|42 Improved| E[Phase E: Cross-Test<br>1890 Runs]
    D -->|33 Not Improved| F[Discarded]
    """
    save_mermaid_png(d1, "S2_D1_Five_Phase_Pipeline")

    d2 = """graph TD
    A[Target Config IPC > Baseline IPC] -->|Yes| B{A: Statistically Significant?<br>Wilcoxon p < 0.25}
    A -->|No| F[No Improvement]
    B -->|Yes| C{B: Practically Significant?<br>Non-zero gain}
    B -->|No| F
    C -->|Yes| D{C: Coverage Preserved?<br>S2 >= S0}
    C -->|No| F
    D -->|Yes| E[IMPROVEMENT DETECTED]
    D -->|No| F
    """
    save_mermaid_png(d2, "S2_D2_Improvement_Decision_Tree")
    
    d3 = """graph TD
    A[Common Template Structure] --> B[Section 1: Role & Core Task]
    A --> C[Section 2: Domain Context]
    A --> D[Section 3: Planner Architecture Info]
    A --> E[Section 4: Reordering Guidelines]
    A --> F[Section 5: Output Constraints]
    
    D --> D1[LAMA: Forward Search, Landmarks, Delete Relaxation]
    D --> D2[DecStar: Factored State Spaces, Leaf States]
    D --> D3[BFWS: Novelty Metric, Width, Counters]
    D --> D4[Madagascar: SAT-based, Makespan, Parallel Length]
    """
    save_mermaid_png(d3, "S2_D3_Prompt_Architecture")

# ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading data for Stage 2...")
    base_df, arch_df, cross_df, llm_df, diff_df, imp_df = load_data()
    print("Generating summaries...")
    generate_summary(llm_df, arch_df, imp_df)
    print("Generating tables and computing IPC matrix...")
    spec_df, verdict_df = generate_tables(base_df, arch_df, cross_df, llm_df, diff_df, imp_df)
    print("Generating graphs...")
    generate_graphs(arch_df, llm_df, imp_df, spec_df, verdict_df)
    print("Generating diagrams...")
    generate_diagrams()
    print("✅ All Stage 2 visual outputs generated successfully!")

if __name__ == "__main__":
    main()
