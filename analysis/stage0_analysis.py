"""
Stage 0 (Baseline) Analysis Script - Visual Output Generator (Academic Thesis Quality)
====================================================================================
Reads planner_execution_data.csv (Stage == BASELINE) and produces:
  1. Formatted Markdown Summaries
  2. Tables as both Markdown and styled PNG images
  3. High-quality academic Graphs (PNGs)
  4. Architectural Diagrams (Mermaid rendered to PNGs)

Organized into: analysis/output/stage0/{1_Summary, 2_Tables, 3_Graphs, 4_Diagrams}
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import io
import os
import base64
import requests
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Paths & Setup ───────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "results" / "planner_execution_data.csv"
OUTPUT_DIR = REPO_ROOT / "analysis" / "output" / "stage0"

DIR_SUMMARY = OUTPUT_DIR / "1_Summary"
DIR_TABLES = OUTPUT_DIR / "2_Tables"
DIR_GRAPHS = OUTPUT_DIR / "3_Graphs"
DIR_DIAGRAMS = OUTPUT_DIR / "4_Diagrams"

for d in [DIR_SUMMARY, DIR_TABLES, DIR_GRAPHS, DIR_DIAGRAMS]:
    d.mkdir(parents=True, exist_ok=True)

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
NUMERIC_COLS = [
    "PlanCost", "Runtime_internal_s", "Runtime_wall_s",
    "StatesExpanded", "StatesGenerated", "StatesEvaluated", "PeakMemoryKB"
]

def load_stage0(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    s0 = df[df["Stage"].str.strip() == "BASELINE"].copy()
    for col in NUMERIC_COLS:
        s0[col] = pd.to_numeric(s0[col], errors="coerce")
    if "Timestamp" in s0.columns:
        s0["Timestamp"] = pd.to_datetime(s0["Timestamp"], errors="coerce")
    return s0

def save_table_png(df: pd.DataFrame, filename: str, title: str):
    if len(df) > 30:
        return # Skip huge tables for PNG
    
    col_width = max(len(str(c)) for c in df.columns) * 0.15 + 1.2
    row_height = 0.5
    size = (len(df.columns) * col_width, (len(df) + 1.5) * row_height)
    
    fig, ax = plt.subplots(figsize=size)
    ax.axis('off')
    
    plt.title(title, fontsize=12, pad=10, weight='bold', fontname='serif')
    
    mpl_table = ax.table(cellText=df.values, bbox=[0, 0, 1, 1], colLabels=df.columns, cellLoc='center')
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(10)
    
    for k, cell in mpl_table._cells.items():
        cell.set_edgecolor('lightgray')
        if k[0] == 0:
            cell.set_text_props(weight='bold', color='white', fontname='serif')
            cell.set_facecolor('#4c72b0') # Academic blue
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
    # Also save as PNG
    save_table_png(df, filename, title)

def save_mermaid_png(mermaid_str: str, filename: str):
    # the API expects the mermaid graph definition without backticks
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

# ─────────────────────────────────────────────────────────────────────
# 1. Summary Statistics
# ─────────────────────────────────────────────────────────────────────
def generate_summary(df: pd.DataFrame):
    success = df[df["Output_Status"] == "SUCCESS"]
    total = len(df)
    n_success = int((df["Output_Status"] == "SUCCESS").sum())
    n_timeout = int((df["Output_Status"] == "TIMEOUT").sum())
    n_memout = int((df["Output_Status"] == "MEMOUT").sum())
    n_failure = int((df["Output_Status"] == "FAILURE").sum())
    solve_rate = round(n_success / total * 100, 2) if total > 0 else 0

    total_pipeline_s = 0
    if "Timestamp" in df.columns and not df["Timestamp"].isna().all():
        total_pipeline_s = (df["Timestamp"].max() - df["Timestamp"].min()).total_seconds()
    else:
        total_pipeline_s = df["Runtime_wall_s"].sum()
    
    hrs = int(total_pipeline_s // 3600)
    mins = int((total_pipeline_s % 3600) // 60)
    secs = int(total_pipeline_s % 60)
    pipeline_str = f"{hrs}h {mins}m {secs}s ({total_pipeline_s:.2f} seconds)"

    content = f"""# S0.1 — Stage 0 Baseline Summary Statistics

## Execution Overview
- **Total Pipeline Runtime:** {pipeline_str}
- **Total Runs:** {total}
- **SUCCESS:** {n_success}
- **TIMEOUT:** {n_timeout}
- **MEMOUT:** {n_memout}
- **FAILURE:** {n_failure}
- **Overall Solve Rate:** **{solve_rate}%**

## Performance Metrics (SUCCESS Runs Only)
- **Mean Wall-Clock Time:** {success['Runtime_wall_s'].mean():.4f} s
- **Median Wall-Clock Time:** {success['Runtime_wall_s'].median():.4f} s
- **Min/Max Wall-Clock Time:** {success['Runtime_wall_s'].min():.4f} s / {success['Runtime_wall_s'].max():.4f} s
- **Mean Plan Cost:** {success['PlanCost'].mean():.4f}
- **Mean Internal Runtime:** {success['Runtime_internal_s'].dropna().mean():.4f} s
"""
    with open(DIR_SUMMARY / "S0_1_Summary_Statistics.md", "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────
# 2. Tables
# ─────────────────────────────────────────────────────────────────────
def generate_tables(df: pd.DataFrame):
    # S0-T1 -- Planner Global Performance Summary
    rows = []
    for p in PLANNERS:
        sub = df[df["Planner_Used"] == p]
        suc = sub[sub["Output_Status"] == "SUCCESS"]
        n = len(sub)
        ns = len(suc)
        row = {
            "Planner": p.upper(), "Total Runs": n, "SUCCESS": ns, "TIMEOUT": int((sub["Output_Status"] == "TIMEOUT").sum()),
            "MEMOUT": int((sub["Output_Status"] == "MEMOUT").sum()), "FAILURE": int((sub["Output_Status"] == "FAILURE").sum()),
            "Solve Rate": f"{ns / n * 100:.2f}%" if n > 0 else "0.00%"
        }
        if ns > 0:
            row["Mean Wall(s)"] = f"{suc['Runtime_wall_s'].mean():.2f}"
            row["Mean Cost"] = f"{suc['PlanCost'].mean():.2f}"
            se = suc["StatesExpanded"].dropna()
            row["Mean States"] = f"{se.mean():.0f}" if len(se) > 0 else "N/R"
        else:
            for k in ["Mean Wall(s)", "Mean Cost", "Mean States"]: row[k] = "N/A"
        rows.append(row)
    t1 = pd.DataFrame(rows)
    save_md_table(t1, "S0_T1_Planner_Summary", "S0-T1: Planner Performance Summary")

    # S0-T2 -- Coverage Matrix
    rows = []
    for d in DOMAINS:
        row = {"Domain": d}
        for p in PLANNERS:
            sub = df[(df["Domain_Name"] == d) & (df["Planner_Used"] == p)]
            row[p.upper()] = f"{int((sub['Output_Status'] == 'SUCCESS').sum())}/{INSTANCES_PER_DOMAIN}"
        rows.append(row)
    t2 = pd.DataFrame(rows)
    save_md_table(t2, "S0_T2_Coverage_Matrix", "S0-T2: Domain x Planner Coverage")

    # S0-T3 -- Mean Wall Time Matrix
    rows = []
    for d in DOMAINS:
        row = {"Domain": d}
        for p in PLANNERS:
            sub = df[(df["Domain_Name"] == d) & (df["Planner_Used"] == p) & (df["Output_Status"] == "SUCCESS")]
            row[p.upper()] = f"{sub['Runtime_wall_s'].mean():.2f}" if len(sub) > 0 else "—"
        rows.append(row)
    t3 = pd.DataFrame(rows)
    save_md_table(t3, "S0_T3_Wall_Time_Matrix", "S0-T3: Mean Wall Time (s)")

    # S0-T4 -- Mean Plan Cost Matrix
    rows = []
    for d in DOMAINS:
        row = {"Domain": d}
        for p in PLANNERS:
            sub = df[(df["Domain_Name"] == d) & (df["Planner_Used"] == p) & (df["Output_Status"] == "SUCCESS")]
            row[p.upper()] = f"{sub['PlanCost'].mean():.2f}" if len(sub) > 0 else "—"
        rows.append(row)
    t4 = pd.DataFrame(rows)
    save_md_table(t4, "S0_T4_Plan_Cost_Matrix", "S0-T4: Mean Plan Cost")

    # S0-T6 -- Domain Difficulty Ranking
    rows = []
    for d in DOMAINS:
        sub = df[df["Domain_Name"] == d]
        suc = sub[sub["Output_Status"] == "SUCCESS"]
        fastest_planner, fastest_time = "—", float("inf")
        for p in PLANNERS:
            p_suc = suc[suc["Planner_Used"] == p]
            if len(p_suc) > 0 and p_suc["Runtime_wall_s"].mean() < fastest_time:
                fastest_planner, fastest_time = p.upper(), p_suc["Runtime_wall_s"].mean()
        
        rows.append({
            "Domain": d, "SUCCESS": len(suc), "Total Runs": len(sub),
            "Solve Rate (%)": f"{len(suc)/len(sub)*100:.1f}%",
            "Fastest Planner": fastest_planner, "Fastest Avg Wall (s)": f"{fastest_time:.2f}" if fastest_time != float("inf") else "—",
        })
    t6 = pd.DataFrame(rows).sort_values("SUCCESS").reset_index(drop=True)
    save_md_table(t6, "S0_T6_Domain_Difficulty", "S0-T6: Domain Difficulty Ranking")

    # S0-T7 -- 5 Tables for Instance Profiles
    for d in DOMAINS:
        d_df = df[df["Domain_Name"] == d]
        instances = sorted(d_df["Problem_Instance"].unique())
        rows_inst = []
        for inst in instances:
            # Shorten instance name for visual table
            short_inst = inst.replace("instance-", "inst-").replace(".pddl", "")
            row = {"Instance": short_inst}
            for p in PLANNERS:
                cell = d_df[(d_df["Problem_Instance"] == inst) & (d_df["Planner_Used"] == p)]
                if len(cell) > 0:
                    status = cell["Output_Status"].values[0]
                    if status == "SUCCESS":
                        row[p.upper()] = f"{cell['Runtime_wall_s'].values[0]:.1f}s"
                    else:
                        row[p.upper()] = "T/O"
                else:
                    row[p.upper()] = "—"
            rows_inst.append(row)
        t7 = pd.DataFrame(rows_inst)
        save_md_table(t7, f"S0_T7_Instance_Profile_{d}", f"S0-T7: {d.capitalize()} Instance Profile")

# ─────────────────────────────────────────────────────────────────────
# 3. Graphs (PNGs) - Academic Style
# ─────────────────────────────────────────────────────────────────────
def generate_graphs(df: pd.DataFrame):
    success = df[df["Output_Status"] == "SUCCESS"].copy()
    success["Planner"] = success["Planner_Used"].str.upper()
    success["Domain"] = success["Domain_Name"].str.capitalize()
    
    academic_palette = sns.color_palette("muted")
    
    # S0-G1: Solve Rate by Planner
    plt.figure(figsize=(7, 5))
    rates = success.groupby("Planner").size() / df.groupby(df["Planner_Used"].str.upper()).size() * 100
    rates = rates.reset_index(name="Solve Rate (%)").sort_values("Solve Rate (%)", ascending=False)
    ax = sns.barplot(x="Planner", y="Solve Rate (%)", data=rates, hue="Planner", palette=academic_palette, legend=False)
    for i, v in enumerate(rates["Solve Rate (%)"]):
        ax.text(i, v + 1, f"{v:.1f}%", ha='center', weight='bold')
    plt.title("Solve Rate by Planner (Baseline)", weight='bold')
    plt.ylim(0, 105)
    sns.despine()
    plt.savefig(DIR_GRAPHS / "S0_G1_Solve_Rate_By_Planner.png")
    plt.close()

    # S0-G2: Heatmap — Coverage Matrix
    cov_matrix = df.groupby(["Domain_Name", "Planner_Used"])["Output_Status"].apply(lambda x: (x == "SUCCESS").sum()).unstack(fill_value=0)
    cov_matrix = cov_matrix.reindex(index=DOMAINS, columns=PLANNERS)
    cov_matrix.index = [d.capitalize() for d in cov_matrix.index]
    cov_matrix.columns = [p.upper() for p in cov_matrix.columns]
    
    plt.figure(figsize=(7, 5))
    sns.heatmap(cov_matrix, annot=True, cmap="YlGnBu", vmin=0, vmax=15, 
                cbar_kws={'label': 'Instances Solved (out of 15)'}, fmt="d")
    plt.title("Coverage Matrix (Instances Solved)", weight='bold', pad=15)
    plt.ylabel("Domain", weight='bold')
    plt.xlabel("Planner", weight='bold')
    plt.tight_layout()
    plt.savefig(DIR_GRAPHS / "S0_G2_Coverage_Heatmap.png")
    plt.close()

    # S0-G3: Box Plot — Runtime by Planner (No Outliers)
    plt.figure(figsize=(7, 5))
    sns.boxplot(x="Planner", y="Runtime_wall_s", data=success, hue="Planner", palette=academic_palette, legend=False, showfliers=False)
    plt.yscale("log")
    plt.title("Runtime Distribution by Planner (Outliers Hidden)", weight='bold')
    plt.ylabel("Wall Time (s) [Log Scale]", weight='bold')
    plt.xlabel("Planner", weight='bold')
    sns.despine()
    plt.savefig(DIR_GRAPHS / "S0_G3_Runtime_By_Planner.png")
    plt.close()

    # S0-G4: Box Plot — Runtime by Domain (No Outliers)
    plt.figure(figsize=(8, 5))
    sns.boxplot(x="Domain", y="Runtime_wall_s", data=success, hue="Domain", palette=academic_palette, legend=False, showfliers=False)
    plt.yscale("log")
    plt.title("Runtime Distribution by Domain (Outliers Hidden)", weight='bold')
    plt.ylabel("Wall Time (s) [Log Scale]", weight='bold')
    plt.xlabel("Domain", weight='bold')
    sns.despine()
    plt.savefig(DIR_GRAPHS / "S0_G4_Runtime_By_Domain.png")
    plt.close()

    # S0-G5: Stacked Bar Chart — Status Distribution
    status_counts = df.groupby([df["Planner_Used"].str.upper(), "Output_Status"]).size().unstack(fill_value=0)
    for s in ["SUCCESS", "TIMEOUT", "MEMOUT", "FAILURE"]:
        if s not in status_counts: status_counts[s] = 0
    status_counts = status_counts[["SUCCESS", "TIMEOUT", "MEMOUT", "FAILURE"]]
    status_pct = status_counts.div(status_counts.sum(axis=1), axis=0) * 100
    
    fig, ax = plt.subplots(figsize=(8, 5))
    status_pct.plot(kind="barh", stacked=True, ax=ax, color=["#4c72b0", "#c44e52", "#ccb974", "#8c8c8c"])
    plt.title("Output Status Distribution by Planner", weight='bold')
    plt.xlabel("Percentage (%)", weight='bold')
    plt.ylabel("Planner", weight='bold')
    plt.legend(title="Output Status", bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    plt.xlim(0, 100)
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    plt.savefig(DIR_GRAPHS / "S0_G5_Status_Distribution.png")
    plt.close()

    # S0-G7: Scatter Plot — Runtime vs Plan Cost (Improved Legend)
    plt.figure(figsize=(9, 6))
    markers = ["o", "s", "D", "^", "v"]
    sns.scatterplot(x="Runtime_wall_s", y="PlanCost", hue="Planner", style="Domain", 
                    data=success, s=120, palette=academic_palette, markers=markers, alpha=0.8)
    plt.xscale("log")
    plt.title("Runtime vs Plan Cost Trade-off", weight='bold')
    plt.xlabel("Wall Time (s) [Log Scale]", weight='bold')
    plt.ylabel("Plan Cost", weight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, title_fontsize='11', fontsize='10')
    sns.despine()
    plt.tight_layout()
    plt.savefig(DIR_GRAPHS / "S0_G7_Runtime_vs_Cost_Scatter.png")
    plt.close()

# ─────────────────────────────────────────────────────────────────────
# 4. Diagrams (Mermaid rendered to PNG)
# ─────────────────────────────────────────────────────────────────────
def generate_diagrams():
    # Pipeline diagram
    d1 = """graph TD
    A[run_stage0.py] -->|Initializes| B[master_orchestrator.py]
    B -->|Spawns Threads| C[Thread Pool]
    C -->|Executes| D1[planner_runner.py LAMA]
    C -->|Executes| D2[planner_runner.py DecStar]
    C -->|Executes| D3[planner_runner.py BFWS]
    C -->|Executes| D4[planner_runner.py Madagascar]
    D1 --> E[Docker Containers isolated environments]
    D2 --> E
    D3 --> E
    D4 --> E
    E -->|Telemetry| F[Thread-safe CSV Manager]
    F -->|Writes to| G[base_planner_execution_data.csv]
"""
    save_mermaid_png(d1, "S0_D1_Pipeline_Architecture")

    # Experimental design mindmap is not well supported in the API without special config,
    # let's use a standard flowchart that looks like a hierarchical tree for compatibility.
    d2 = """graph LR
    A((Stage 0 Baseline)) --> B(Domains)
    B --> B1[visitall]
    B --> B2[snake]
    B --> B3[ricochet-robots]
    B --> B4[depots]
    B --> B5[barman]
    A --> C(Planners)
    C --> C1[LAMA]
    C --> C2[DecStar]
    C --> C3[BFWS]
    C --> C4[Madagascar]
    A --> D(Instances)
    D --> D1[15 per Domain]
    A --> E(Total Runs)
    E --> E1[300]
"""
    save_mermaid_png(d2, "S0_D2_Experimental_Design")

# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading data...")
    df = load_stage0(DATA_FILE)
    print("Generating 1_Summary...")
    generate_summary(df)
    print("Generating 2_Tables...")
    generate_tables(df)
    print("Generating 3_Graphs...")
    generate_graphs(df)
    print("Generating 4_Diagrams...")
    generate_diagrams()
    print("✅ All Stage 0 visual outputs (Academic Style) generated successfully!")

if __name__ == "__main__":
    main()
