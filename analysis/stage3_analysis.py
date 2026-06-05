import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import os
import base64
import requests

# =============================================================================
# Configuration & Paths
# =============================================================================
PROJECT_ROOT = Path("c:/Users/danie/My Drive/ArchAware-PDDL-Configurator")

RESULTS_DIR = PROJECT_ROOT / "results"
FEEDBACK_DIR = RESULTS_DIR / "feedback_loop"
VAL_METRICS_DIR = PROJECT_ROOT / "validation_and_evaluation" / "data" / "production"

ITER_TRACKING_CSV = FEEDBACK_DIR / "iteration_tracking.csv"
FINAL_DOMAINS_CSV = FEEDBACK_DIR / "stage3_final_domains.csv"
S3_DIFF_METRICS_CSV = VAL_METRICS_DIR / "feedback_loop" / "feedback_loop_pddl_diff_metrics.csv"
S2_DIFF_METRICS_CSV = VAL_METRICS_DIR / "arch_aware" / "arch_aware_pddl_diff_metrics.csv"
LLM_GEN_CSV = FEEDBACK_DIR / "feedback_loop_llm_generation_data.csv"

OUTPUT_DIR = PROJECT_ROOT / "analysis" / "output" / "stage3"
DIR_SUMMARY = OUTPUT_DIR / "1_Summary"
DIR_TABLES = OUTPUT_DIR / "2_Tables"
DIR_GRAPHS = OUTPUT_DIR / "3_Graphs"
DIR_DIAGRAMS = OUTPUT_DIR / "4_Diagrams"

sns.set_theme(style="whitegrid", context="talk")

def ensure_dirs():
    for d in [DIR_SUMMARY, DIR_TABLES, DIR_GRAPHS, DIR_DIAGRAMS]:
        d.mkdir(parents=True, exist_ok=True)

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
    print(f"Saved Table & PNG: {filename}")

def safe_savefig(filename: str):
    path = DIR_GRAPHS / f"{filename}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved Graph: {filename}")

def write_diagram(filename: str, content: str):
    clean_str = content.strip().replace("```mermaid", "").replace("```", "").strip()
    try:
        b64 = base64.b64encode(clean_str.encode('utf-8')).decode('ascii')
        url = f"https://mermaid.ink/img/{b64}"
        resp = requests.get(url)
        resp.raise_for_status()
        with open(DIR_DIAGRAMS / f"{filename}.png", 'wb') as f:
            f.write(resp.content)
        print(f"Saved Diagram PNG: {filename}")
    except Exception as e:
        print(f"Failed to generate Diagram {filename}.png: {e}")

def load_data():
    df_iter = pd.read_csv(ITER_TRACKING_CSV) if ITER_TRACKING_CSV.exists() else pd.DataFrame()
    df_final = pd.read_csv(FINAL_DOMAINS_CSV) if FINAL_DOMAINS_CSV.exists() else pd.DataFrame()
    df_s3_diff = pd.read_csv(S3_DIFF_METRICS_CSV) if S3_DIFF_METRICS_CSV.exists() else pd.DataFrame()
    df_s2_diff = pd.read_csv(S2_DIFF_METRICS_CSV) if S2_DIFF_METRICS_CSV.exists() else pd.DataFrame()
    PLANNER_EXEC_CSV = FEEDBACK_DIR / "feedback_loop_planner_execution_data.csv"
    LLM_GEN_CSV = FEEDBACK_DIR / "feedback_loop_llm_generation_data.csv"
    PLANNER_ERR_CSV = PROJECT_ROOT / "logs" / "stage3" / "error_register.csv"
    LLM_ERR_CSV = PROJECT_ROOT / "logs" / "stage3" / "LLM_run" / "error_register.csv"
    df_planner = pd.read_csv(PLANNER_EXEC_CSV) if PLANNER_EXEC_CSV.exists() else pd.DataFrame()
    df_llm = pd.read_csv(LLM_GEN_CSV) if LLM_GEN_CSV.exists() else pd.DataFrame()
    df_planner_err = pd.read_csv(PLANNER_ERR_CSV) if PLANNER_ERR_CSV.exists() else pd.DataFrame()
    df_llm_err = pd.read_csv(LLM_ERR_CSV) if LLM_ERR_CSV.exists() else pd.DataFrame()
    
    # Pre-compute Baseline_IPC_Score in df_final
    if not df_iter.empty and not df_final.empty:
        df_baseline = df_iter.groupby(['Domain', 'LLM', 'Target_Planner']).first().reset_index()
        df_baseline['Baseline_IPC_Score'] = df_baseline['IPC_Score'] - df_baseline['Delta_vs_Baseline']
        df_final = pd.merge(df_final, df_baseline[['Domain', 'LLM', 'Target_Planner', 'Baseline_IPC_Score']], on=['Domain', 'LLM', 'Target_Planner'], how='left')
        
    return df_iter, df_final, df_s3_diff, df_s2_diff, df_planner, df_llm, df_planner_err, df_llm_err

# =============================================================================
# Section 1: Execution Summary (T1)
# =============================================================================
def generate_summary(df_iter, df_final, df_planner, df_llm, df_planner_err, df_llm_err):
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)]
    contestable = len(df_contestable)
    improved = len(df_contestable[df_contestable['Best_Iteration'] > 0])
    
    t1 = pd.DataFrame([
        {"Metric": "Total triples processed", "Value": len(df_final)},
        {"Metric": "Always-timeout triples (excluded)", "Value": len(df_final) - contestable},
        {"Metric": "Contestable triples", "Value": contestable},
        {"Metric": "Triples improved vs. seed", "Value": improved},
        {"Metric": "Improvement rate (contestable)", "Value": f"{(improved/contestable*100):.1f}%" if contestable>0 else "0%"},
        {"Metric": "Total iterations executed", "Value": len(df_iter)},
        {"Metric": "Mean iterations per triple", "Value": f"{(len(df_iter)/len(df_final)):.2f}"},
        {"Metric": "Total planner runs", "Value": len(df_planner)},
        {"Metric": "Total LLM API calls", "Value": len(df_llm)},
        {"Metric": "Total pipeline runtime", "Value": "~37 hours"},
        {"Metric": "LLM errors (total)", "Value": len(df_llm_err)},
        {"Metric": "Planner errors (total)", "Value": len(df_planner_err)}
    ])
    save_md_table(t1, "S3_T1_Execution_Summary", "S3-T1: High-Level Execution Summary")
    
    summary_md = "# S3.1 & S3.8 — Stage 3 Summary\n\n"
    summary_md += "## Execution Summary\n"
    summary_md += f"- **Total Triples Processed:** {len(df_final)}\n"
    summary_md += f"- **Contestable Triples:** {contestable}\n"
    summary_md += f"- **Triples Improved vs. Seed:** {improved}\n"
    summary_md += f"- **Total Iterations Executed:** {len(df_iter)}\n"
    summary_md += f"- **Total Planner Runs:** {len(df_planner)}\n"
    summary_md += f"- **Total LLM API Calls:** {len(df_llm)}\n"
    
    with open(DIR_SUMMARY / "S3_1_Summary.md", "w", encoding="utf-8") as f:
        f.write(summary_md)
    print("Saved Summary MD: S3_1_Summary.md")

# =============================================================================
# Section 2: Improvement Analysis vs Seed (T2-T4, G1-G3)
# =============================================================================
def analyze_improvement(df_final):
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)].copy()
    
    imp_llm = df_contestable.groupby('LLM').apply(
        lambda x: pd.Series({
            "Contestable_Triples": len(x),
            "Improved": (x['Best_Iteration'] > 0).sum(),
            "Rate (%)": f"{(x['Best_Iteration'] > 0).mean() * 100:.1f}%"
        })
    ).reset_index().sort_values('Rate (%)', ascending=False)
    save_md_table(imp_llm, "S3_T2_Improvement_by_LLM", "S3-T2: Improvement by LLM (Contestable)")
    
    plt.figure(figsize=(10,6))
    imp_llm['Rate_Num'] = imp_llm['Rate (%)'].str.replace('%','').astype(float)
    sns.barplot(data=imp_llm, x='LLM', y='Rate_Num', hue='LLM', palette='viridis', legend=False)
    plt.xticks(fontsize=8)
    plt.title("S3-G1: Improvement Rate by LLM")
    plt.ylabel("Improvement Rate (%)")
    safe_savefig("S3_G1_Improvement_by_LLM")
    
    imp_planner = df_contestable.groupby('Target_Planner').apply(
        lambda x: pd.Series({
            "Contestable": len(x),
            "Improved": (x['Best_Iteration'] > 0).sum(),
            "Rate (%)": f"{(x['Best_Iteration'] > 0).mean() * 100:.1f}%"
        })
    ).reset_index().sort_values('Rate (%)', ascending=False)
    save_md_table(imp_planner, "S3_T3_Improvement_by_Planner", "S3-T3: Improvement by Planner (Contestable)")
    
    plt.figure(figsize=(10,6))
    imp_planner['Rate_Num'] = imp_planner['Rate (%)'].str.replace('%','').astype(float)
    sns.barplot(data=imp_planner, x='Target_Planner', y='Rate_Num', hue='Target_Planner', palette='plasma', legend=False)
    plt.title("S3-G2: Improvement Rate by Planner")
    plt.ylabel("Improvement Rate (%)")
    safe_savefig("S3_G2_Improvement_by_Planner")
    
    imp_domain = df_contestable.groupby('Domain').apply(
        lambda x: pd.Series({
            "Contestable": len(x),
            "Improved": (x['Best_Iteration'] > 0).sum(),
            "Rate (%)": f"{(x['Best_Iteration'] > 0).mean() * 100:.1f}%"
        })
    ).reset_index().sort_values('Rate (%)', ascending=False)
    save_md_table(imp_domain, "S3_T4_Improvement_by_Domain", "S3-T4: Improvement by Domain (Contestable)")
    
    plt.figure(figsize=(10,6))
    imp_domain['Rate_Num'] = imp_domain['Rate (%)'].str.replace('%','').astype(float)
    sns.barplot(data=imp_domain, x='Domain', y='Rate_Num', hue='Domain', palette='magma', legend=False)
    plt.title("S3-G3: Improvement Rate by Domain")
    plt.ylabel("Improvement Rate (%)")
    safe_savefig("S3_G3_Improvement_by_Domain")

# =============================================================================
# Section 3: Iteration-Level Analysis (T5-T8, G4, G5, G10)
# =============================================================================
def analyze_iterations(df_final, df_iter):
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)].copy()
    
    # T5
    b_iter = df_contestable['Best_Iteration'].value_counts().reset_index()
    b_iter.columns = ['Best Iteration', 'Count (contestable)']
    b_iter['Percentage'] = (b_iter['Count (contestable)'] / b_iter['Count (contestable)'].sum() * 100).apply(lambda x: f"{x:.1f}%")
    b_iter = b_iter.sort_values('Best Iteration')
    save_md_table(b_iter, "S3_T5_Best_Iteration", "S3-T5: Best Iteration Distribution")
    
    plt.figure(figsize=(8,8))
    labels = [f"Iter {i}" if i>0 else "Seed Best" for i in b_iter['Best Iteration']]
    plt.pie(b_iter['Count (contestable)'], labels=labels, autopct='%1.1f%%', colors=sns.color_palette("pastel"))
    plt.title("S3-G4: Best Iteration Distribution")
    safe_savefig("S3_G4_Best_Iteration_Pie")
    
    # T6
    term = df_final['Termination_Reason'].value_counts().reset_index()
    term.columns = ['Reason', 'Count']
    if 'LLM_ERROR' not in term['Reason'].values:
        term = pd.concat([term, pd.DataFrame([{'Reason': 'LLM_ERROR', 'Count': 0}])], ignore_index=True)
    term['Percentage'] = (term['Count'] / term['Count'].sum() * 100).apply(lambda x: f"{x:.1f}%")
    save_md_table(term, "S3_T6_Termination_Reason", "S3-T6: Termination Reason Distribution")
    
    plt.figure(figsize=(8,8))
    plt.pie(term[term['Count']>0]['Count'], labels=term[term['Count']>0]['Reason'], autopct='%1.1f%%', colors=sns.color_palette("Set2"))
    plt.title("S3-G5: Termination Reason Distribution")
    safe_savefig("S3_G5_Termination_Reasons")
    
    # T7
    t7_data = []
    iter_merged = pd.merge(df_iter, df_final[['Domain', 'LLM', 'Target_Planner', 'Seed_IPC_Score', 'Baseline_IPC_Score']], on=['Domain', 'LLM', 'Target_Planner'], how='left')
    for i in [1, 2, 3]:
        i_df = iter_merged[iter_merged['Iteration'] == i]
        if i_df.empty: continue
        valid = i_df[i_df['Validation_Status'] == 'VALID']
        improved_base = valid[valid['Improved'] == True]
        
        # Improved vs Seed can be strictly better IPC OR a tie-breaker (same IPC but Is_Best_So_Far is True, typically for time optimization)
        # However, for Iteration 1 it compares against Seed.
        improved_seed = valid[
            (valid['IPC_Score'] > valid['Seed_IPC_Score']) | 
            ((valid['IPC_Score'] == valid['Seed_IPC_Score']) & (valid['Is_Best_So_Far'] == True))
        ]
        t7_data.append({
            "Iteration": i,
            "Total Executed": len(i_df),
            "Valid Domains Produced": len(valid),
            "Valid & Improved vs Baseline": len(improved_base),
            "Valid & Improved vs Seed": len(improved_seed)
        })
    save_md_table(pd.DataFrame(t7_data), "S3_T7_Iter_Improvement", "S3-T7: Iteration-Level Improvement Rates (Valid Iterations Only)")
    
    # T8
    patterns = {"Get it right first try": 0, "Progressive refinement": 0, "Late bloomer": 0, "Stuck at seed": 0}
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)]
    contestable_keys = set(zip(df_contestable['Domain'], df_contestable['LLM'], df_contestable['Target_Planner']))
    for name, group in iter_merged.groupby(['Domain', 'LLM', 'Target_Planner']):
        if name not in contestable_keys: continue
        group = group.sort_values('Iteration')
        if group.empty: continue
        best = df_final[(df_final['Domain']==name[0]) & (df_final['LLM']==name[1]) & (df_final['Target_Planner']==name[2])]['Best_Iteration'].iloc[0]
        if best == 0:
            patterns["Stuck at seed"] += 1
        elif best == 1:
            patterns["Get it right first try"] += 1
        else:
            # Check if it was strictly progressively refined (Is_Best_So_Far is True for all 3 iterations)
            is_best_list = group['Is_Best_So_Far'].tolist()
            if is_best_list == [True, True, True]:
                patterns["Progressive refinement"] += 1
            else:
                patterns["Late bloomer"] += 1
            
    t8_data = [
        {"Pattern": "Get it right first try", "Count": patterns["Get it right first try"], "Description": "Iter 1 improves, iters 2-3 may regress"},
        {"Pattern": "Progressive refinement", "Count": patterns["Progressive refinement"], "Description": "Valid & improves vs previous on ALL 3 iterations"},
        {"Pattern": "Late bloomer", "Count": patterns["Late bloomer"], "Description": "Peaks at Iter 2 or 3, without continuous improvement"},
        {"Pattern": "Stuck at seed", "Count": patterns["Stuck at seed"], "Description": "No iteration beats the seed"}
    ]
    t8 = pd.DataFrame(t8_data)
    save_md_table(t8, "S3_T8_Convergence_Patterns", "S3-T8: Convergence Pattern Classification")
    
    plt.figure(figsize=(10,6))
    sns.barplot(data=t8, x='Pattern', y='Count', hue='Pattern', palette='crest', legend=False)
    plt.title("S3-G10: Convergence Pattern Distribution")
    plt.xticks(rotation=15)
    safe_savefig("S3_G10_Convergence_Pattern")

# =============================================================================
# Section 4: Stage 2 Recovery (T9, T10, G6)
# =============================================================================
def analyze_recovery(df_final):
    if 'Was_Stage2_Failure' not in df_final.columns: return
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)].copy()
    
    rec_data = [
        {"Was_Stage2_Failure": False, "Contestable": 63, "Improved vs Seed": 27, "Improved vs Baseline": 52},
        {"Was_Stage2_Failure": True, "Contestable": 5, "Improved vs Seed": 5, "Improved vs Baseline": 3}
    ]
    rec = pd.DataFrame(rec_data)
    
    rec['Improved vs Seed Rate (%)'] = (rec['Improved vs Seed'] / rec['Contestable'] * 100).apply(lambda x: f"{x:.1f}%")
    rec['Improved vs Baseline Rate (%)'] = (rec['Improved vs Baseline'] / rec['Contestable'] * 100).apply(lambda x: f"{x:.1f}%")
    rec = rec[['Was_Stage2_Failure', 'Contestable', 'Improved vs Seed', 'Improved vs Seed Rate (%)', 'Improved vs Baseline', 'Improved vs Baseline Rate (%)']]
    save_md_table(rec, "S3_T9_Stage2_Recovery", "S3-T9: Stage 2 Failure Recovery")
    
    # G6
    plt.figure(figsize=(8,6))
    rec['Rate_Num'] = rec['Improved vs Seed Rate (%)'].str.replace('%','').astype(float)
    rec['Seed_Status'] = rec['Was_Stage2_Failure'].map({True: "Failed Seed", False: "Valid Seed"})
    sns.barplot(data=rec, x='Seed_Status', y='Rate_Num', hue='Seed_Status', palette='Blues', legend=False)
    plt.title("S3-G6: Stage 2 Recovery (Improvement vs Seed Rate)")
    plt.ylabel("Improvement Rate (%)")
    safe_savefig("S3_G6_Stage2_Recovery")
    
    # T10
    failed_seeds = df_contestable[df_contestable['Was_Stage2_Failure'] == True].copy()
    failed_seeds['Better than Baseline?'] = failed_seeds['Best_IPC_Score'] > failed_seeds['Baseline_IPC_Score']
    t10 = failed_seeds[['Domain', 'LLM', 'Target_Planner', 'Best_Iteration', 'Best_IPC_Score', 'Improvement_vs_Seed', 'Better than Baseline?']]
    save_md_table(t10, "S3_T10_Recovery_Cases", "S3-T10: Specific Recovery Cases")

# =============================================================================
# Section 5: Validation Failures (T11-T13, G12, G13)
# =============================================================================
def analyze_validation(df_iter):
    # T11
    total = len(df_iter)
    valid = len(df_iter[df_iter['Validation_Status'] == 'VALID'])
    failed = total - valid
    v4_count = len(df_iter[df_iter['Validation_Status'] == 'INVALID_V4'])
    v1_count = len(df_iter[df_iter['Validation_Status'] == 'INVALID_V1'])
    token_count = len(df_iter[df_iter['Validation_Status'] == 'LLM_TokenLimitExceeded'])
    
    t11 = pd.DataFrame([
        {"Metric": "Total iterations", "Value": total},
        {"Metric": "Valid iterations", "Value": valid},
        {"Metric": "Failed iterations", "Value": failed},
        {"Metric": "Validation success rate", "Value": f"{(valid/total*100):.1f}%"},
        {"Metric": "V4 semantic failures", "Value": v4_count},
        {"Metric": "V1 extraction failures", "Value": v1_count},
        {"Metric": "LLM TokenLimitExceeded", "Value": token_count}
    ])
    save_md_table(t11, "S3_T11_Validation_Summary", "S3-T11: Validation Failure Summary")
    
    # T12
    # Hardcoded based on user manual verification of failures per iteration (including Stage 2 / Iteration 0)
    t12_data = [
        {"Iteration": 0, "Total Failures": 5, "Validation Failures": 2, "LLM Failures": 3},
        {"Iteration": 1, "Total Failures": 5, "Validation Failures": 5, "LLM Failures": 0},
        {"Iteration": 2, "Total Failures": 7, "Validation Failures": 6, "LLM Failures": 1},
        {"Iteration": 3, "Total Failures": 9, "Validation Failures": 6, "LLM Failures": 3}
    ]
    t12 = pd.DataFrame(t12_data)
    save_md_table(t12, "S3_T12_Failures_per_Triple", "S3-T12: Validation & LLM Failures per Iteration")
    
    # T13
    if 'V4_Failure_Detail' in df_iter.columns:
        def filter_v4(detail_str):
            if pd.isna(detail_str): return detail_str
            try:
                d = eval(detail_str) if isinstance(detail_str, str) else detail_str
                d_filtered = {k: v for k, v in d.items() if 'reordered' not in k}
                return str(d_filtered)
            except:
                return detail_str
                
        v4 = df_iter[df_iter['Validation_Status'] == 'INVALID_V4'].copy()
        v4['Semantic Changes'] = v4['V4_Failure_Detail'].apply(filter_v4)
        t13 = v4[['Domain', 'LLM', 'Target_Planner', 'Iteration', 'Semantic Changes']]
        save_md_table(t13, "S3_T13_V4_Failures", "S3-T13: V4 Semantic Failure Details")
        
    # G12
    fail_rates = df_iter.groupby('Iteration').apply(
        lambda x: (x['Validation_Status'] != 'VALID').mean() * 100
    ).reset_index(name='Failure_Rate')
    plt.figure(figsize=(8,6))
    sns.barplot(data=fail_rates, x='Iteration', y='Failure_Rate', hue='Iteration', palette='Reds', legend=False)
    plt.title("S3-G12: Validation Failure Rate by Iteration")
    plt.ylabel("Failure Rate (%)")
    safe_savefig("S3_G12_Validation_Failure_Rate")
    if 'Validation_Status' in df_iter.columns:
        fails = df_iter[df_iter['Validation_Status'] != 'VALID']['Validation_Status'].value_counts().reset_index()
        fails.columns = ['Failure_Type', 'Count']
        plt.figure(figsize=(10, 6))
        sns.barplot(data=fails, x='Failure_Type', y='Count', hue='Failure_Type', palette='Set2', legend=False)
        plt.title("S3-G13: Validation Failure Types Distribution")
        plt.xticks(rotation=15)
        safe_savefig("S3_G13_Validation_Failure_Types_Distribution")

# =============================================================================
# Section 6: Token Usage (T14-T15, G7)
# =============================================================================
def analyze_token_usage(df_iter):
    t14 = df_iter.groupby('LLM').agg(
        Avg_Input_Tokens=('LLM_Input_Tokens', 'mean'),
        Avg_Output_Tokens=('LLM_Output_Tokens', 'mean'),
        Total_Input=('LLM_Input_Tokens', 'sum'),
        Total_Output=('LLM_Output_Tokens', 'sum')
    ).round(0).reset_index()
    save_md_table(t14, "S3_T14_Token_Usage_Overall", "S3-T14: Token Usage by LLM")
    
    trend = df_iter.pivot_table(index='LLM', columns='Iteration', values=['LLM_Input_Tokens', 'LLM_Output_Tokens'], aggfunc='mean').round(0).fillna(0)
    cols = []
    for c in trend.columns:
        if c[0] == 'LLM_Input_Tokens': cols.append(f"Iter {c[1]} Avg In")
        else: cols.append(f"Iter {c[1]} Avg Out")
    trend.columns = cols
    ordered_cols = ['Iter 1 Avg In', 'Iter 1 Avg Out', 'Iter 2 Avg In', 'Iter 2 Avg Out', 'Iter 3 Avg In', 'Iter 3 Avg Out']
    ordered_cols = [c for c in ordered_cols if c in trend.columns]
    trend = trend[ordered_cols].reset_index()
    save_md_table(trend, "S3_T15_Token_Usage_Trend", "S3-T15: Token Usage Trend Across Iterations")

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_iter, x='Iteration', y='LLM_Input_Tokens', hue='LLM', marker='o', errorbar=None)
    plt.title("S3-G7: Input Token Growth Across Iterations")
    plt.legend(bbox_to_anchor=(0.5, -0.25), loc='upper center', ncol=2, borderaxespad=0.)
    plt.xticks([1, 2, 3])
    safe_savefig("S3_G7_Input_Token_Trend")

# =============================================================================
# Section 7: Best Domain (T16-T18, G8, G9, G11)
# =============================================================================
def analyze_best_domains(df_final, df_iter):
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)]
    t16 = pd.DataFrame([
        {"Metric": "Mean Best_IPC_Score (contestable)", "Value": df_contestable['Best_IPC_Score'].mean()},
        {"Metric": "Median Best_IPC_Score (contestable)", "Value": df_contestable['Best_IPC_Score'].median()},
        {"Metric": "Min Best_IPC_Score (contestable)", "Value": df_contestable['Best_IPC_Score'].min()},
        {"Metric": "Max Best_IPC_Score (contestable)", "Value": df_contestable['Best_IPC_Score'].max()},
        {"Metric": "Mean Seed_IPC_Score (contestable)", "Value": df_contestable['Seed_IPC_Score'].mean()},
        {"Metric": "Mean Improvement_vs_Seed (contestable)", "Value": df_contestable['Improvement_vs_Seed'].mean()}
    ])
    save_md_table(t16, "S3_T16_IPC_Distribution", "S3-T16: IPC Score Distribution of Best Domains (Contestable)")
    
    t17 = df_final.sort_values('Improvement_vs_Seed', ascending=False).head(10).copy()
    t17['Rank'] = range(1, 11)
    t17.rename(columns={'Seed_IPC_Score': 'Seed IPC', 'Best_IPC_Score': 'Best IPC', 'Improvement_vs_Seed': 'Improvement', 'Best_Iteration': 'Best Iter'}, inplace=True)
    t17 = t17[['Rank', 'Domain', 'LLM', 'Target_Planner', 'Seed IPC', 'Best IPC', 'Improvement', 'Best Iter']]
    save_md_table(t17, "S3_T17_Top10_Improvements", "S3-T17: Top 10 Largest Improvements vs Seed")
    
    # T18
    t18_c = df_contestable[df_contestable['Best_Iteration'] == 0].copy()
    gaps = []
    for _, r in t18_c.iterrows():
        m = df_iter[(df_iter['Domain']==r['Domain'])&(df_iter['LLM']==r['LLM'])&(df_iter['Target_Planner']==r['Target_Planner'])]
        best_i_row = m.loc[m['IPC_Score'].idxmax()] if not m.empty else None
        best_i_ipc = best_i_row['IPC_Score'] if best_i_row is not None else 0
        best_i = best_i_row['Iteration'] if best_i_row is not None else 0
        gaps.append({
            'Domain': r['Domain'], 
            'LLM': r['LLM'], 
            'Target_Planner': r['Target_Planner'], 
            'Seed IPC': r['Seed_IPC_Score'], 
            'Best Iteration IPC': best_i_ipc, 
            'Regression': r['Seed_IPC_Score'] - best_i_ipc, 
            'Best Iter': best_i
        })
    t18 = pd.DataFrame(gaps).sort_values('Regression', ascending=False).head(10).copy()
    t18['Rank'] = range(1, len(t18) + 1)
    t18 = t18[['Rank', 'Domain', 'LLM', 'Target_Planner', 'Seed IPC', 'Best Iteration IPC', 'Regression', 'Best Iter']]
    save_md_table(t18, "S3_T18_Top10_Regressions", "S3-T18: Top 10 Largest Regressions vs Seed")
    
    # G8
    plt.figure(figsize=(10,6))
    sns.histplot(df_final['Best_IPC_Score'], bins=15, kde=True, color='purple')
    plt.title("S3-G8: Best IPC Score Distribution")
    safe_savefig("S3_G8_Best_IPC_Hist")
    
    # G9
    plt.figure(figsize=(10,6))
    improved_data = df_final[df_final['Best_Iteration'] > 0]['Improvement_vs_Seed']
    sns.histplot(improved_data, bins=15, kde=True, color='teal')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.title("S3-G9: Improvement vs. Seed Distribution (Improved Domains Only)")
    safe_savefig("S3_G9_Improvement_Hist")
    
    # G11
    heatmap_data = df_final.pivot_table(index='Domain', columns='Target_Planner', values='Best_Iteration', aggfunc=lambda x: x.mode().iloc[0] if not x.mode().empty else 0).fillna(0)
    plt.figure(figsize=(8,6))
    sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", cbar_kws={'label': 'Most Common Best Iteration'})
    plt.title("S3-G11: Best Iteration by (Domain × Planner)")
    safe_savefig("S3_G11_Best_Iter_Heatmap")

# =============================================================================
# Section 8: Combined Stage 2+3 (T19-T20)
# =============================================================================
def analyze_combined_efficacy(df_final, df_iter):
    t19 = pd.DataFrame([
        {"Metric": "Contestable triples", "Value": 68},
        {"Metric": "Triples improved vs. Stage 0 baseline", "Value": 55},
        {"Metric": "Combined improvement rate", "Value": "80.9%"},
        {"Metric": "Improvements from seed (Stage 2)", "Value": 30},
        {"Metric": "Additional improvements from iterations", "Value": 25}
    ])
    save_md_table(t19, "S3_T19_Combined_Efficacy", "S3-T19: Stage 2+3 Combined Efficacy vs Stage 0 Baseline")
    
    t20 = pd.DataFrame([
        {"Source of Best Domain": "Seed (Stage 2)", "Count (of 55 that beat baseline)": 30},
        {"Source of Best Domain": "Iteration 1", "Count (of 55 that beat baseline)": 12},
        {"Source of Best Domain": "Iteration 2", "Count (of 55 that beat baseline)": 5},
        {"Source of Best Domain": "Iteration 3", "Count (of 55 that beat baseline)": 8}
    ])
    save_md_table(t20, "S3_T20_Best_Iter_Source", "S3-T20: Best Iteration Source for Baseline-Improving Domains")

# =============================================================================
# Section 9: The Critical Additions (T21, T22, G14)
# =============================================================================
def analyze_critical_additions(df_final, df_iter, df_s2_diff, df_s3_diff):
    # T21
    import json as _json
    
    def extract_planner(path):
        if pd.isna(path): return None
        if 'Arch_Aware' in path:
            return path.split('_')[-1].replace('.json', '')
        elif 'feedback_loop' in path:
            return path.split('__')[-1].split('_')[0]
        return None

    df_s2_diff = df_s2_diff.copy()
    df_s2_diff['Target_Planner'] = df_s2_diff['json_report_path'].apply(extract_planner)
    
    df_s3_diff = df_s3_diff.copy()
    df_s3_diff['Target_Planner'] = df_s3_diff['json_report_path'].apply(extract_planner)

    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)]
    improved = df_contestable[df_contestable['Best_Iteration'] > 0]
    
    # Map component names to the suffixes used in the JSON syntactic diff type field
    component_suffixes = {
        'requirements': ['requirements-order'],
        'type': ['types-order', 'type-order'],
        'predicates': ['predicates-order'],
        'function': ['functions-order', 'function-order'],
        'actions': ['actions-order'],
        'parameters': ['params-order'],
        'preconditions': ['precondition-order'],
        'add effects': ['eff-add-order'],
        'delete effects': ['eff-del-order']
    }
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def count_reorders_from_json(json_path):
        """Count actual reorder entries per component by reading the JSON file."""
        counts = {comp: 0 for comp in component_suffixes}
        full_path = os.path.join(BASE_DIR, json_path)
        if not os.path.exists(full_path):
            return counts
        try:
            with open(full_path) as f:
                d = _json.load(f)
            syns = d.get('diff_details', {}).get('syntactic', [])
            for s in syns:
                t = s.get('type', '')
                for comp, suffixes in component_suffixes.items():
                    for suffix in suffixes:
                        if t.endswith(suffix):
                            counts[comp] += 1
                            break
        except:
            pass
        return counts
    
    results_t21 = {comp: {'domains_seed': 0, 'domains_best': 0, 'reorders_seed': 0, 'reorders_best': 0} for comp in component_suffixes}
    
    for _, row in improved.iterrows():
        dom, llm, planner, best_iter = row['Domain'], row['LLM'], row['Target_Planner'], row['Best_Iteration']
        
        seed_row = df_s2_diff[(df_s2_diff['domain'] == dom) & (df_s2_diff['LLM_Model'] == llm) & 
                              (df_s2_diff['Target_Planner'] == planner)]
        best_row = df_s3_diff[(df_s3_diff['domain'] == dom) & (df_s3_diff['LLM_Model'] == llm) & 
                              (df_s3_diff['Target_Planner'] == planner) & (df_s3_diff['stage'] == f'Feedback_Loop{best_iter}')]
        
        if not seed_row.empty and pd.notna(seed_row.iloc[0]['json_report_path']):
            seed_counts = count_reorders_from_json(seed_row.iloc[0]['json_report_path'])
            for comp, cnt in seed_counts.items():
                if cnt > 0:
                    results_t21[comp]['domains_seed'] += 1
                    results_t21[comp]['reorders_seed'] += cnt
        
        if not best_row.empty and pd.notna(best_row.iloc[0]['json_report_path']):
            best_counts = count_reorders_from_json(best_row.iloc[0]['json_report_path'])
            for comp, cnt in best_counts.items():
                if cnt > 0:
                    results_t21[comp]['domains_best'] += 1
                    results_t21[comp]['reorders_best'] += cnt
    
    res21 = []
    for comp in component_suffixes:
        r = results_t21[comp]
        res21.append({
            "PDDL Component": comp,
            "Domains Reordered in Seed": r['domains_seed'],
            "Domains Reordered in Best Iteration": r['domains_best'],
            "Total Reorders in Seed": r['reorders_seed'],
            "Total Reorders in Best Iteration": r['reorders_best']
        })
        
    save_md_table(pd.DataFrame(res21), "S3_T21_Structural_Shifts", "S3-T21: Reordering Component Shifts (Improved vs Seed)")



    # G14
    tokens = df_iter.groupby(['Domain', 'LLM', 'Target_Planner']).agg(Total_Output=('LLM_Output_Tokens', 'sum')).reset_index()
    roi_df = pd.merge(tokens, df_final, on=['Domain', 'LLM', 'Target_Planner'])
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=roi_df, x='Total_Output', y='Improvement_vs_Seed', hue='LLM', s=100, alpha=0.8, palette="viridis")
    plt.title("S3-G14: ROI - Token Cost vs. IPC Gain")
    plt.axhline(0, color='red', linestyle='--')
    safe_savefig("S3_G14_ROI_Scatter")

# =============================================================================
# Section 10: Diagrams (D1, D2, D3)
# =============================================================================
def write_diagrams():
    d1 = """```mermaid\ngraph TD\nA[LLM Call] --> B[Extract Rationale]\nB --> C[Hard Critics V1-V4]\nC -- Valid --> D[Soft Critics / Planner]\nC -- Invalid --> F[Update History / Validation Feedback]\nD --> E[Build Telemetry]\nE --> F\nF --> G[Next Iteration]\n```"""
    write_diagram("S3_D1_Feedback_Architecture", d1)
    
    d2 = """```mermaid
graph TD
    A[Stage 2 Output Domain] --> B{"What is the Domain Status?"}
    
    B -->|6A: API Error| C[No PDDL Generated]
    C --> D[Send to Stage 3 Feedback Loop<br>Goal: Recover from Stage 2 Token Limit]
    
    B -->|6B: Valid Seed| E[Evaluate Seed IPC Score]
    E --> F[Send to Stage 3 Feedback Loop<br>Goal: Improve IPC Score]
    
    B -->|6C: Invalid Seed| G[Seed IPC Score = 0]
    G --> H[Send to Stage 3 Feedback Loop<br>Goal: Stage 2 Failure Recovery]
```"""
    write_diagram("S3_D2_Seed_Routing", d2)
    
    d3 = """```mermaid\ngraph LR\nA[Controller] --> B[Thread 1: GPT]\nA --> C[Thread 2: Claude]\nA --> D[Thread 3: Gemini]\nA --> E[Thread 4: DeepSeek]\n```"""
    write_diagram("S3_D3_Parallel_Pipelines", d3)

# =============================================================================
# Section 11: Additional Insights (T22-T26, G15-G18)
# =============================================================================
def analyze_additional_insights(df_final, df_iter, df_planner):
    df_contestable = df_final[(df_final['Seed_IPC_Score'] != 0) | (df_final['Best_IPC_Score'] != 0)].copy()
    
    # -------------------------------------------------------------------------
    # T22: Planner Solve Rate by Iteration
    # -------------------------------------------------------------------------
    if not df_planner.empty:
        solve_rows = []
        for stage in sorted(df_planner['Stage'].unique()):
            sub = df_planner[df_planner['Stage'] == stage]
            total = len(sub)
            success = (sub['Output_Status'] == 'SUCCESS').sum()
            timeout = (sub['Output_Status'] == 'TIMEOUT').sum()
            failure = (sub['Output_Status'] == 'FAILURE').sum()
            solve_rows.append({
                "Iteration": stage.replace("Feedback_Loop", "Iteration "),
                "Total Runs": total,
                "SUCCESS": success,
                "TIMEOUT": timeout,
                "FAILURE": failure,
                "Solve Rate (%)": f"{success/total*100:.1f}%"
            })
        t22 = pd.DataFrame(solve_rows)
        save_md_table(t22, "S3_T22_Planner_Solve_Rate", "S3-T22: Planner Solve Rate by Iteration")
        
        # G15: Line Chart — Solve Rate Trend
        plt.figure(figsize=(10, 6))
        t22['Rate_Num'] = t22['Solve Rate (%)'].str.replace('%','').astype(float)
        plt.plot(t22['Iteration'], t22['Rate_Num'], marker='o', linewidth=2.5, color='#2ca02c', markersize=10)
        for i, row in t22.iterrows():
            plt.annotate(f"{row['Rate_Num']:.1f}%", (row['Iteration'], row['Rate_Num']),
                         textcoords="offset points", xytext=(0, 12), ha='center', fontsize=11, fontweight='bold')
        plt.title("S3-G15: Planner Solve Rate Across Iterations")
        plt.ylabel("Solve Rate (%)")
        plt.xlabel("Iteration")
        plt.ylim(bottom=50)
        safe_savefig("S3_G15_Solve_Rate_Trend")
    
    # -------------------------------------------------------------------------
    # T23: Mean IPC Score Progression by LLM
    # -------------------------------------------------------------------------
    if not df_iter.empty:
        ipc_prog = df_iter.groupby(['LLM', 'Iteration'])['IPC_Score'].mean().unstack()
        ipc_prog.columns = [f"Iter {c} Mean IPC" for c in ipc_prog.columns]
        ipc_prog = ipc_prog.reset_index()
        # Round values
        for c in ipc_prog.columns[1:]:
            ipc_prog[c] = ipc_prog[c].round(2)
        save_md_table(ipc_prog, "S3_T23_IPC_Progression", "S3-T23: Mean IPC Score Progression by LLM")
        
        # G16: Line Chart — IPC Progression by LLM
        plt.figure(figsize=(10, 6))
        ipc_data = df_iter.groupby(['LLM', 'Iteration'])['IPC_Score'].mean().reset_index()
        sns.lineplot(data=ipc_data, x='Iteration', y='IPC_Score', hue='LLM', marker='o', errorbar=None)
        plt.title("S3-G16: Mean IPC Score Progression by LLM")
        plt.ylabel("Mean IPC Score")
        plt.xlabel("Iteration")
        plt.xticks([1, 2, 3])
        plt.legend(bbox_to_anchor=(0.5, -0.25), loc='upper center', ncol=2, borderaxespad=0.)
        safe_savefig("S3_G16_IPC_Progression_by_LLM")
    
    # -------------------------------------------------------------------------
    # T24: Improvement Rate by Domain × Planner (Contestable)
    # -------------------------------------------------------------------------
    df_contestable['improved'] = df_contestable['Best_Iteration'] > 0
    pivot = df_contestable.groupby(['Domain', 'Target_Planner']).apply(
        lambda x: f"{x['improved'].sum()}/{len(x)}"
    ).unstack(fill_value='N/A')
    pivot = pivot.reset_index()
    pivot.columns.name = None
    save_md_table(pivot, "S3_T24_Domain_Planner_Improvement", "S3-T24: Improvement Rate by Domain × Planner (Contestable)")
    
    # G17: Heatmap — Improvement Rate Domain × Planner
    pivot_num = df_contestable.groupby(['Domain', 'Target_Planner'])['improved'].mean().unstack(fill_value=0)
    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_num * 100, annot=True, fmt='.0f', cmap='YlGn',
                cbar_kws={'label': 'Improvement Rate (%)'}, linewidths=0.5)
    plt.title("S3-G17: Improvement Rate by Domain × Planner (%)")
    plt.ylabel("Domain")
    plt.xlabel("Target Planner")
    safe_savefig("S3_G17_Domain_Planner_Heatmap")
    
    # -------------------------------------------------------------------------
    # T25: Output Token Efficiency (Cost per IPC Point)
    # -------------------------------------------------------------------------
    if not df_iter.empty:
        token_eff = df_iter.groupby('LLM').agg(
            Total_Output_Tokens=('LLM_Output_Tokens', 'sum'),
            Mean_Output_Tokens=('LLM_Output_Tokens', 'mean')
        ).reset_index()
        
        # Get mean improvement per LLM from df_final contestable
        llm_imp = df_contestable.groupby('LLM').agg(
            Mean_Improvement_vs_Seed=('Improvement_vs_Seed', 'mean'),
            Improved_Count=('improved', 'sum'),
            Total_Triples=('improved', 'count')
        ).reset_index()
        
        token_eff = pd.merge(token_eff, llm_imp, on='LLM')
        token_eff['Tokens_per_IPC_Point'] = token_eff.apply(
            lambda r: f"{r['Total_Output_Tokens']/r['Mean_Improvement_vs_Seed']:.0f}" if r['Mean_Improvement_vs_Seed'] > 0 else 'N/A', axis=1
        )
        token_eff['Improvement_Rate'] = token_eff.apply(
            lambda r: f"{r['Improved_Count']/r['Total_Triples']*100:.1f}%", axis=1
        )
        token_eff['Total_Output_Tokens'] = token_eff['Total_Output_Tokens'].apply(lambda x: f"{x:,}")
        token_eff['Mean_Output_Tokens'] = token_eff['Mean_Output_Tokens'].apply(lambda x: f"{x:,.0f}")
        token_eff['Mean_Improvement_vs_Seed'] = token_eff['Mean_Improvement_vs_Seed'].round(3)
        
        t25 = token_eff[['LLM', 'Total_Output_Tokens', 'Mean_Output_Tokens', 'Improvement_Rate', 'Mean_Improvement_vs_Seed', 'Tokens_per_IPC_Point']]
        t25.columns = ['LLM', 'Total Output Tokens', 'Mean Output Tokens', 'Improvement Rate', 'Mean Improvement vs Seed', 'Tokens per IPC Point']
        save_md_table(t25, "S3_T25_Token_Efficiency", "S3-T25: Output Token Efficiency by LLM")
    
    # -------------------------------------------------------------------------
    # T26: LLM × Domain Improvement Matrix
    # -------------------------------------------------------------------------
    llm_domain = df_contestable.groupby(['LLM', 'Domain']).apply(
        lambda x: f"{x['improved'].sum()}/{len(x)}"
    ).unstack(fill_value='N/A')
    llm_domain = llm_domain.reset_index()
    llm_domain.columns.name = None
    save_md_table(llm_domain, "S3_T26_LLM_Domain_Matrix", "S3-T26: Improvement Rate by LLM × Domain (Contestable)")
    
    # G18: Heatmap — LLM × Domain Improvement Rate
    llm_domain_num = df_contestable.groupby(['LLM', 'Domain'])['improved'].mean().unstack(fill_value=0)
    plt.figure(figsize=(10, 6))
    sns.heatmap(llm_domain_num * 100, annot=True, fmt='.0f', cmap='YlOrRd',
                cbar_kws={'label': 'Improvement Rate (%)'}, linewidths=0.5)
    plt.title("S3-G18: Improvement Rate by LLM × Domain (%)")
    plt.ylabel("LLM")
    plt.xlabel("Domain")
    plt.xticks(fontsize=9)
    plt.yticks(fontsize=8)
    safe_savefig("S3_G18_LLM_Domain_Heatmap")

    # -------------------------------------------------------------------------
    # T27: Planner Solve Rate by Iteration and Planner
    # -------------------------------------------------------------------------
    if not df_planner.empty:
        solve_by_planner = []
        for stage in sorted(df_planner['Stage'].unique()):
            for planner in sorted(df_planner['Planner_Used'].unique()):
                sub = df_planner[(df_planner['Stage'] == stage) & (df_planner['Planner_Used'] == planner)]
                if len(sub) == 0:
                    continue
                total = len(sub)
                success = (sub['Output_Status'] == 'SUCCESS').sum()
                solve_by_planner.append({
                    "Iteration": stage.replace("Feedback_Loop", "Iter "),
                    "Planner": planner,
                    "Solve Rate (%)": round(success/total*100, 1)
                })
        t27_df = pd.DataFrame(solve_by_planner)
        t27_pivot = t27_df.pivot(index='Planner', columns='Iteration', values='Solve Rate (%)')
        t27_pivot = t27_pivot.reset_index()
        t27_pivot.columns.name = None
        save_md_table(t27_pivot, "S3_T27_Solve_Rate_by_Planner", "S3-T27: Planner Solve Rate by Iteration and Planner (%)")

# =============================================================================
# Main
# =============================================================================
def main():
    print("=" * 60)
    print("   STAGE 3 - FEEDBACK LOOP ANALYSIS GENERATION")
    print("=" * 60)
    ensure_dirs()
    df_iter, df_final, df_s3_diff, df_s2_diff, df_planner, df_llm, df_planner_err, df_llm_err = load_data()
    
    generate_summary(df_iter, df_final, df_planner, df_llm, df_planner_err, df_llm_err)
    analyze_improvement(df_final)
    analyze_iterations(df_final, df_iter)
    analyze_recovery(df_final)
    analyze_validation(df_iter)
    analyze_token_usage(df_iter)
    analyze_best_domains(df_final, df_iter)
    analyze_combined_efficacy(df_final, df_iter)
    analyze_critical_additions(df_final, df_iter, df_s2_diff, df_s3_diff)
    analyze_additional_insights(df_final, df_iter, df_planner)
    write_diagrams()
    print("\n[SUCCESS] Stage 3 Analysis completed.")

if __name__ == "__main__":
    main()

