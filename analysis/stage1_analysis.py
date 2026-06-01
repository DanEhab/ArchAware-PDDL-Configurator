"""
Stage 1 (General Prompt) Analysis Script - Visual Output Generator
====================================================================================
Reads Stage 1 data and produces:
  1. Formatted Markdown Summaries
  2. Tables as both Markdown and styled PNG images
  3. High-quality academic Graphs (PNGs)
  4. Architectural Diagrams (Mermaid rendered to PNGs)

Organized into: analysis/output/stage1/{1_Summary, 2_Tables, 3_Graphs, 4_Diagrams}
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
OUTPUT_DIR = REPO_ROOT / "analysis" / "output" / "stage1"

DIR_SUMMARY = OUTPUT_DIR / "1_Summary"
DIR_TABLES = OUTPUT_DIR / "2_Tables"
DIR_GRAPHS = OUTPUT_DIR / "3_Graphs"
DIR_DIAGRAMS = OUTPUT_DIR / "4_Diagrams"

for d in [DIR_SUMMARY, DIR_TABLES, DIR_GRAPHS, DIR_DIAGRAMS]:
    d.mkdir(parents=True, exist_ok=True)

# Data files
PLANNER_EXEC_CSV = REPO_ROOT / "results" / "planner_execution_data.csv"
LLM_GEN_CSV = REPO_ROOT / "results" / "general_prompt" / "LLM Results" / "general_llm_generation_data.csv"
DIFF_METRICS_CSV = REPO_ROOT / "validation_and_evaluation" / "data" / "production" / "general_prompt" / "general_pddl_diff_metrics.csv"

# Set academic theme for all graphs
sns.set_theme(style="ticks", context="paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['font.family'] = 'serif'

# ── Constants ──────────────────────────────────────────────────────────
PLANNERS = ["bfws", "lama", "decstar", "madagascar"]
DOMAINS = ["visitall", "snake", "ricochet-robots", "depots", "barman"]
INSTANCES_PER_DOMAIN = 15

LLM_SHORT_NAMES = {
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "deepseek-reasoner": "DeepSeek-R1",
    "claude-opus-4-6": "Claude 4.6",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1",
}

NUMERIC_COLS = [
    "PlanCost", "Runtime_internal_s", "Runtime_wall_s",
    "StatesExpanded", "StatesGenerated", "StatesEvaluated", "PeakMemoryKB"
]

REORDER_COLS = [
    "req_reordered", "type_reordered", "pred_reordered", "func_reordered",
    "actions_reordered", "params_reordered", "pre_reordered",
    "eff_add_reordered", "eff_del_reordered"
]

COMPONENT_LABELS = [
    "Requirements", "Types", "Predicates", "Functions",
    "Actions", "Parameters", "Preconditions", "Add Effects", "Delete Effects"
]

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
    if len(df) > 35:
        return # Skip huge tables for PNG
    
    col_width = max(len(str(c)) for c in df.columns) * 0.15 + 1.0
    row_height = 0.5
    size = (len(df.columns) * col_width, (len(df) + 1.5) * row_height)
    
    fig, ax = plt.subplots(figsize=size)
    ax.axis('off')
    
    plt.title(title, fontsize=12, pad=10, weight='bold', fontname='serif')
    
    # Render emojis properly by avoiding issues, or ignoring in matplotlib
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
    planner_df = pd.read_csv(PLANNER_EXEC_CSV)
    planner_df = planner_df[planner_df["Stage"].str.strip().str.upper() == "GENERAL"].copy()
    for col in NUMERIC_COLS:
        planner_df[col] = pd.to_numeric(planner_df[col], errors="coerce")
    
    llm_df = pd.read_csv(LLM_GEN_CSV) if LLM_GEN_CSV.exists() else pd.DataFrame()
    diff_df = pd.read_csv(DIFF_METRICS_CSV) if DIFF_METRICS_CSV.exists() else pd.DataFrame()
    
    return planner_df, llm_df, diff_df

def get_actual_reorder_count(json_path_str: str) -> int:
    if pd.isna(json_path_str): return 0
    
    # Fix incorrect relative path in the CSV
    if "data/production/diffs/" in json_path_str:
        json_path_str = json_path_str.replace("data/production/diffs/", "data/production/general_prompt/diffs/")
        
    p = REPO_ROOT / json_path_str
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                return len(data.get("diff_details", {}).get("syntactic", []))
        except:
            pass
    return 0

# ─────────────────────────────────────────────────────────────────────
# 1. Summary Statistics
# ─────────────────────────────────────────────────────────────────────
def generate_summary(planner_df: pd.DataFrame, llm_df: pd.DataFrame, diff_df: pd.DataFrame):
    content = "# S1.1 & S1.2 — Stage 1 General Prompt Summaries\n\n"
    
    if not llm_df.empty:
        api_time = pd.to_numeric(llm_df.get("LLM API Time S", llm_df.get("LLM_API_Time_S")), errors="coerce")
        content += f"## LLM API Summary\n"
        content += f"- **Total Calls:** {len(llm_df)}\n"
        content += f"- **Mean API Time:** {api_time.mean():.2f} s\n"
        in_tok = pd.to_numeric(llm_df.get("Input Tokens Consumed"), errors="coerce").sum()
        out_tok = pd.to_numeric(llm_df.get("Output Tokens Generated", llm_df.get("Output tokens consumed")), errors="coerce").sum()
        content += f"- **Total Tokens:** {(in_tok + out_tok):,.0f}\n"
        content += f"- **Total Input Tokens:** {in_tok:,.0f}\n"
        content += f"- **Total Output Tokens:** {out_tok:,.0f}\n\n"
        
    if not planner_df.empty:
        success = planner_df[planner_df["Output_Status"] == "SUCCESS"]
        content += f"## Planner Execution Summary\n"
        content += f"- **Total Runs:** {len(planner_df)}\n"
        content += f"- **Overall Solve Rate:** {(len(success)/len(planner_df)*100):.2f}% ({len(success)}/{len(planner_df)})\n"
        content += f"- **Mean Wall Time (SUCCESS):** {success['Runtime_wall_s'].mean():.2f} s\n"
    
    with open(DIR_SUMMARY / "S1_1_Summary.md", "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────
# 2. Tables
# ─────────────────────────────────────────────────────────────────────
def generate_tables(planner_df: pd.DataFrame, llm_df: pd.DataFrame, diff_df: pd.DataFrame):
    # S1-T1: LLM API Performance
    if not llm_df.empty:
        rows = []
        llm_df["Short_LLM"] = llm_df["LLM Model"].apply(shorten_llm)
        for llm in llm_df["Short_LLM"].unique():
            sub = llm_df[llm_df["Short_LLM"] == llm]
            in_tok = pd.to_numeric(sub.get("Input Tokens Consumed"), errors="coerce")
            out_tok = pd.to_numeric(sub.get("Output Tokens Generated", sub.get("Output tokens consumed")), errors="coerce")
            api_time = pd.to_numeric(sub.get("LLM API Time S"), errors="coerce")
            rows.append({
                "LLM Model": llm,
                "API Calls": len(sub),
                "Successful": len(sub[sub["LLM_Status"].str.lower() == "passed"]),
                "Mean API Time (s)": f"{api_time.mean():.1f}",
                "Input Tokens": f"{in_tok.sum():,.0f}",
                "Output Tokens": f"{out_tok.sum():,.0f}",
                "Total Tokens": f"{(in_tok.sum() + out_tok.sum()):,.0f}",
                "Tokens/Domain (Avg)": f"{out_tok.mean():,.0f}"
            })
        t1 = pd.DataFrame(rows)
        save_md_table(t1, "S1_T1_LLM_API_Performance", "S1-T1: LLM API Performance")
        
        # S1-T2: Token Usage Breakdown
        pivot = llm_df.pivot_table(index="Domain Name", columns="Short_LLM", 
                                  values=["Input Tokens Consumed", "Output Tokens Generated"], aggfunc="sum")
        rows2 = []
        for d in DOMAINS:
            if d not in pivot.index: continue
            row = {"Domain": d.capitalize()}
            for llm in t1["LLM Model"]:
                try:
                    i = pivot.loc[d, ("Input Tokens Consumed", llm)]
                    o = pivot.loc[d, ("Output Tokens Generated", llm)]
                    if pd.notna(i) and pd.notna(o):
                        row[llm] = f"{int(i)} / {int(o)}"
                    else:
                        row[llm] = "—"
                except KeyError:
                    row[llm] = "—"
            rows2.append(row)
        if rows2:
            save_md_table(pd.DataFrame(rows2), "S1_T2_Token_Breakdown", "S1-T2: Token Usage (In/Out)")

        # S1-T3: Validation Status
        valid = int((llm_df["Validation Status"].str.lower() == "valid").sum())
        rej_v1 = len(llm_df[(llm_df["Passed Stage V1"] == "False") | (llm_df["Passed Stage V1"] == False)])
        rej_v2 = len(llm_df[(llm_df["Passed VAL Syntactic Check (V2)"] == "False") | (llm_df["Passed VAL Syntactic Check (V2)"] == False)])
        rej_v3 = len(llm_df[(llm_df["Passed V3"] == "False") | (llm_df["Passed V3"] == False)])
        inv_v4 = len(llm_df[(llm_df["Validation Status"].str.lower()=="invalid") | (llm_df["Passed V4"] == "False") | (llm_df["Passed V4"] == False)])
        
        t3 = pd.DataFrame([
            {"Status": "Total files processed", "Count": len(llm_df)},
            {"Status": "VALID (passed V1-V4)", "Count": valid},
            {"Status": "REJECTED at V1 (Extraction)", "Count": rej_v1},
            {"Status": "REJECTED at V2 (Syntax)", "Count": rej_v2},
            {"Status": "REJECTED at V3 (Identity)", "Count": rej_v3},
            {"Status": "INVALID at V4 (Semantic)", "Count": inv_v4},
        ])
        t3["Pass rate (%)"] = [f"{(c/len(llm_df)*100):.1f}%" for c in t3["Count"]]
        save_md_table(t3, "S1_T3_Validation_Summary", "S1-T3: Validation Outcome Summary")
        
        # S1-T4: Validation Matrix
        rows4 = []
        for d in DOMAINS:
            row = {"Domain": d.capitalize()}
            for llm in t1["LLM Model"]:
                sub = llm_df[(llm_df["Domain Name"] == d) & (llm_df["Short_LLM"] == llm)]
                if len(sub) > 0:
                    status = sub["Validation Status"].iloc[0].upper()
                    if status == "VALID":
                        row[llm] = "PASS"
                    else:
                        v1 = sub["Passed Stage V1"].iloc[0]
                        v2 = sub["Passed VAL Syntactic Check (V2)"].iloc[0]
                        v3 = sub["Passed V3"].iloc[0]
                        v4 = sub["Passed V4"].iloc[0]
                        reason = "(V1)" if v1 in ["False", False] else \
                                 "(V2)" if v2 in ["False", False] else \
                                 "(V3)" if v3 in ["False", False] else \
                                 "(V4)" if v4 in ["False", False] else ""
                        row[llm] = f"FAIL {reason}"
                else:
                    row[llm] = "—"
            rows4.append(row)
        save_md_table(pd.DataFrame(rows4), "S1_T4_Validation_Matrix", "S1-T4: Validation Status Matrix")

    # S1-T5, S1-T6, S1-T7: Reordering
    if not diff_df.empty:
        valid_df = diff_df[diff_df["validation_status"].str.lower() == "valid"].copy()
        valid_df["Short_LLM"] = valid_df["LLM_Model"].apply(shorten_llm)
        
        # S1-T5: PDDL Component Reordering Patterns
        t5_cols = ["domain", "Short_LLM"] + [c for c in REORDER_COLS if c in valid_df.columns]
        t5 = valid_df[t5_cols].copy()
        t5.columns = ["Domain", "LLM"] + [COMPONENT_LABELS[i] for i, c in enumerate(REORDER_COLS) if c in valid_df.columns]
        t5["Domain"] = t5["Domain"].str.capitalize()
        for col in t5.columns[2:]:
            t5[col] = t5[col].apply(lambda x: "1" if pd.to_numeric(x, errors='coerce') == 1 else "0")
        save_md_table(t5, "S1_T5_Reordering_Patterns", "S1-T5: PDDL Component Reordering Patterns")
        
        # S1-T6: Reordering Frequency
        rows6 = []
        total_valid = len(valid_df)
        for col, label in zip(REORDER_COLS, COMPONENT_LABELS):
            if col in valid_df.columns:
                cnt = pd.to_numeric(valid_df[col]).sum()
                rows6.append({"Component": label, "Times Reordered": int(cnt), "Percentage": f"{(cnt/total_valid*100):.1f}%" if total_valid>0 else "0%"})
        t6 = pd.DataFrame(rows6).sort_values("Times Reordered", ascending=False)
        save_md_table(t6, "S1_T6_Reordering_Frequency", "S1-T6: Reordering Frequency")
        
        # S1-T7: Reordering Aggressiveness (Actual count from JSON)
        rows7 = []
        valid_df["actual_reorder_count"] = valid_df["json_report_path"].apply(get_actual_reorder_count)
        
        for llm in valid_df["Short_LLM"].unique():
            sub = valid_df[valid_df["Short_LLM"] == llm]
            actual_count = sub["actual_reorder_count"].sum()
            
            # Most frequent component category
            max_c, max_val = "None", 0
            for c, label in zip(REORDER_COLS, COMPONENT_LABELS):
                if c in sub.columns:
                    val = pd.to_numeric(sub[c]).sum()
                    if val > max_val: max_c, max_val = label, val
                    
            rows7.append({
                "LLM": llm,
                "Total Reordered Items (JSON)": int(actual_count),
                "Avg Reorders Per Domain": f"{(actual_count/len(sub)):.1f}",
                "Most Frequently Touched Component": max_c
            })
        t7 = pd.DataFrame(rows7).sort_values("Total Reordered Items (JSON)", ascending=False)
        save_md_table(t7, "S1_T7_Reorder_By_LLM", "S1-T7: Reordering Aggressiveness by LLM")

    # S1-T8: Planner Summary
    if not planner_df.empty:
        rows8 = []
        for p in PLANNERS:
            sub = planner_df[planner_df["Planner_Used"] == p]
            suc = sub[sub["Output_Status"] == "SUCCESS"]
            if len(sub) == 0: continue
            rows8.append({
                "Planner": p.upper(),
                "Total Runs": len(sub),
                "SUCCESS": len(suc),
                "TIMEOUT": len(sub[sub["Output_Status"] == "TIMEOUT"]),
                "Solve Rate": f"{(len(suc)/len(sub)*100):.1f}%",
                "Mean Wall (s)": f"{suc['Runtime_wall_s'].mean():.2f}" if len(suc)>0 else "—",
                "Mean Cost": f"{suc['PlanCost'].mean():.2f}" if len(suc)>0 else "—"
            })
        t8 = pd.DataFrame(rows8)
        save_md_table(t8, "S1_T8_Planner_Summary", "S1-T8: Global Planner Performance (Stage 1)")

        # S1-T9: Coverage Matrix Planner x Domain x LLM
        planner_df["Short_LLM"] = planner_df["LLM_Used"].apply(shorten_llm)
        rows9 = []
        # Find all valid Domain/LLM pairs
        pairs = planner_df[["Domain_Name", "Short_LLM"]].drop_duplicates()
        for _, r in pairs.iterrows():
            d = r["Domain_Name"]
            llm = r["Short_LLM"]
            row = {"Domain": d.capitalize(), "LLM": llm}
            for p in PLANNERS:
                sub = planner_df[(planner_df["Domain_Name"] == d) & (planner_df["Short_LLM"] == llm) & (planner_df["Planner_Used"] == p)]
                suc = sub[sub["Output_Status"] == "SUCCESS"]
                if len(sub) > 0:
                    row[f"{p.upper()} Cov"] = f"{len(suc)}/15"
                    row[f"{p.upper()} AvgTime"] = f"{suc['Runtime_wall_s'].mean():.2f}s" if len(suc) > 0 else "—"
                else:
                    row[f"{p.upper()} Cov"] = "—"
                    row[f"{p.upper()} AvgTime"] = "—"
            rows9.append(row)
        t9 = pd.DataFrame(rows9).sort_values(["Domain", "LLM"])
        save_md_table(t9, "S1_T9_Coverage_Matrix", "S1-T9: Coverage Matrix (Planner × Domain × LLM)")

        # S1-T10 & S1-T11: Timeout Distributions
        rows10 = []
        for d in DOMAINS:
            sub = planner_df[planner_df["Domain_Name"] == d]
            if len(sub) == 0: continue
            to = len(sub[sub["Output_Status"] == "TIMEOUT"])
            rows10.append({"Domain": d.capitalize(), "Timeouts": to, "Pct of Domain": f"{(to/len(sub)*100):.1f}%"})
        save_md_table(pd.DataFrame(rows10).sort_values("Timeouts", ascending=False), "S1_T10_Timeout_By_Domain", "S1-T10: Timeouts by Domain")

        rows11 = []
        for p in PLANNERS:
            sub = planner_df[planner_df["Planner_Used"] == p]
            if len(sub) == 0: continue
            to = len(sub[sub["Output_Status"] == "TIMEOUT"])
            rows11.append({"Planner": p.upper(), "Timeouts": to, "Pct of Planner": f"{(to/len(sub)*100):.1f}%"})
        save_md_table(pd.DataFrame(rows11).sort_values("Timeouts", ascending=False), "S1_T11_Timeout_By_Planner", "S1-T11: Timeouts by Planner")


# ─────────────────────────────────────────────────────────────────────
# 3. Graphs
# ─────────────────────────────────────────────────────────────────────
def generate_graphs(planner_df: pd.DataFrame, llm_df: pd.DataFrame, diff_df: pd.DataFrame):
    academic_palette = sns.color_palette("muted")

    if not llm_df.empty:
        llm_df["Short_LLM"] = llm_df["LLM Model"].apply(shorten_llm)
        
        # S1-G1: LLM Token Usage
        plt.figure(figsize=(8, 5))
        tok_data = llm_df.groupby("Short_LLM")[["Input Tokens Consumed", "Output Tokens Generated"]].sum().reset_index()
        tok_melt = tok_data.melt(id_vars="Short_LLM", var_name="Type", value_name="Tokens")
        tok_melt["Type"] = tok_melt["Type"].str.replace(" Consumed", "").str.replace(" Generated", "")
        sns.barplot(x="Short_LLM", y="Tokens", hue="Type", data=tok_melt, palette=["#4c72b0", "#dd8452"])
        plt.title("Token Usage by LLM (Stage 1)", weight='bold')
        plt.ylabel("Total Tokens", weight='bold')
        plt.xlabel("LLM", weight='bold')
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S1_G1_Token_Usage.png")
        plt.close()

        # S1-G2: Validation Pie Chart
        plt.figure(figsize=(6, 6))
        val_counts = llm_df["Validation Status"].str.upper().value_counts()
        colors = {"VALID": "#55a868", "REJECTED": "#c44e52", "INVALID": "#ccb974"}
        plot_colors = [colors.get(idx, "gray") for idx in val_counts.index]
        plt.pie(val_counts, labels=val_counts.index, autopct='%1.1f%%', colors=plot_colors, startangle=140, textprops={'weight': 'bold'})
        plt.title("Validation Outcomes", weight='bold')
        plt.savefig(DIR_GRAPHS / "S1_G2_Validation_Pie.png")
        plt.close()

    if not diff_df.empty:
        valid_df = diff_df[diff_df["validation_status"].str.lower() == "valid"].copy()
        valid_df["Short_LLM"] = valid_df["LLM_Model"].apply(shorten_llm)
        
        # S1-G3: Reordering Heatmap (Clearer version)
        matrix = []
        y_labels = []
        for _, row in valid_df.iterrows():
            y_labels.append(f"{row['domain'].capitalize()} ({row['Short_LLM']})")
            matrix.append([pd.to_numeric(row.get(c, 0)) for c in REORDER_COLS])
        
        if matrix:
            plt.figure(figsize=(10, len(matrix)*0.3 + 2))
            cmap = mcolors.ListedColormap(['#ffffff', '#2ca02c'])
            sns.heatmap(matrix, cmap=cmap, cbar=False, linewidths=1.0, linecolor='lightgray',
                        xticklabels=COMPONENT_LABELS, yticklabels=y_labels)
            plt.title("PDDL Component Reordering Matrix", weight='bold', pad=15)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(DIR_GRAPHS / "S1_G3_Reordering_Heatmap.png")
            plt.close()

        # S1-G4: Reordering Frequency Bar
        freq = [sum(m[i] for m in matrix) for i in range(len(COMPONENT_LABELS))]
        freq_df = pd.DataFrame({"Component": COMPONENT_LABELS, "Count": freq}).sort_values("Count", ascending=False)
        plt.figure(figsize=(8, 5))
        sns.barplot(x="Count", y="Component", data=freq_df, color="#55a868")
        plt.title("Reordering Frequency by Component", weight='bold')
        plt.xlabel("Number of Domains Modified", weight='bold')
        plt.ylabel("")
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S1_G4_Reordering_Frequency.png")
        plt.close()

    if not planner_df.empty:
        planner_df["Planner"] = planner_df["Planner_Used"].str.upper()
        planner_df["Short_LLM"] = planner_df["LLM_Used"].apply(shorten_llm)
        success = planner_df[planner_df["Output_Status"] == "SUCCESS"]
        
        # S1-G5: Solve Rate by Planner
        plt.figure(figsize=(7, 5))
        rates = success.groupby("Planner").size() / planner_df.groupby("Planner").size() * 100
        rates = rates.reset_index(name="Solve Rate (%)").sort_values("Solve Rate (%)", ascending=False)
        ax = sns.barplot(x="Planner", y="Solve Rate (%)", data=rates, hue="Planner", palette=academic_palette, legend=False)
        for i, v in enumerate(rates["Solve Rate (%)"]): ax.text(i, v + 1, f"{v:.1f}%", ha='center', weight='bold')
        plt.title("Solve Rate by Planner (Stage 1)", weight='bold')
        plt.ylim(0, 105)
        sns.despine()
        plt.savefig(DIR_GRAPHS / "S1_G5_Solve_Rate_Planner.png")
        plt.close()

        # S1-G6: Heatmap — Coverage Matrix (LLM × Domain)
        cov_matrix = success.groupby(["Domain_Name", "Short_LLM"]).size().unstack(fill_value=0) / (4 * 15) * 100 # avg across 4 planners
        cov_matrix = cov_matrix.reindex(index=DOMAINS).T
        cov_matrix.columns = [d.capitalize() for d in cov_matrix.columns]
        
        plt.figure(figsize=(8, 4))
        sns.heatmap(cov_matrix, annot=True, cmap="YlGnBu", vmin=0, vmax=100, fmt=".1f", cbar_kws={'label': 'Average Solve Rate (%)'})
        plt.title("Coverage Matrix Averaged Across Planners", weight='bold', pad=15)
        plt.ylabel("LLM", weight='bold')
        plt.xlabel("Domain", weight='bold')
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S1_G6_Coverage_LLM_Domain_Heatmap.png")
        plt.close()

        # S1-G7: Grouped Bar Chart — Planner Solve Rate Comparison (Includes Overall)
        plt.figure(figsize=(12, 6))
        # Overall solve rate per planner
        overall_rates = success.groupby("Planner").size() / planner_df.groupby("Planner").size() * 100
        overall_df = overall_rates.reset_index(name="Solve Rate (%)")
        overall_df["LLM"] = "All LLMs Combined"
        
        # LLM specific solve rate per planner
        llm_rates = success.groupby(["Planner", "Short_LLM"]).size() / planner_df.groupby(["Planner", "Short_LLM"]).size() * 100
        llm_rates = llm_rates.reset_index(name="Solve Rate (%)")
        llm_rates.rename(columns={"Short_LLM": "LLM"}, inplace=True)
        
        combined_rates = pd.concat([overall_df, llm_rates], ignore_index=True)
        
        sns.barplot(x="Planner", y="Solve Rate (%)", hue="LLM", data=combined_rates, palette=sns.color_palette("Set2"))
        plt.title("Planner Solve Rate Comparison", weight='bold')
        plt.ylim(0, 105)
        plt.legend(title="LLM Generator", bbox_to_anchor=(1.05, 1), loc='upper left')
        sns.despine()
        plt.tight_layout()
        plt.savefig(DIR_GRAPHS / "S1_G7_Grouped_Solve_Rate.png")
        plt.close()

# ─────────────────────────────────────────────────────────────────────
# 4. Diagrams
# ─────────────────────────────────────────────────────────────────────
def generate_diagrams():
    d1 = """graph LR
    A[Phase A: LLM Generation<br>20 PDDL Files] --> B[Phase B: Validation<br>V1-V4 Semantic]
    B -->|18 Pass| C[Phase C: Planner Execution]
    B -->|2 Fail| D[Discarded]
    C -->|18 * 4 Planners * 15 Instances| E[1080 Planner Runs]
    """
    save_mermaid_png(d1, "S1_D1_Three_Phase_Pipeline")

    d2 = """graph TD
    A[Raw LLM Output] -->|V1: Extraction| B{Valid Block?}
    B -->|Yes| C{V2: Syntax Check}
    B -->|No| F[REJECTED V1]
    C -->|Pass| D{V3: Identity Check}
    C -->|Fail| G[REJECTED V2]
    D -->|Different from Base| E{V4: Semantic Diff}
    D -->|Identical| H[REJECTED V3]
    E -->|Only formatting changes| I[VALID]
    E -->|Illegal logic change| J[INVALID V4]
    """
    save_mermaid_png(d2, "S1_D2_Validation_Flow")

# ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading data for Stage 1...")
    planner_df, llm_df, diff_df = load_data()
    print("Generating summaries...")
    generate_summary(planner_df, llm_df, diff_df)
    print("Generating tables...")
    generate_tables(planner_df, llm_df, diff_df)
    print("Generating graphs...")
    generate_graphs(planner_df, llm_df, diff_df)
    print("Generating diagrams...")
    generate_diagrams()
    print("✅ All Stage 1 visual outputs (Academic Style) generated successfully!")

if __name__ == "__main__":
    main()
