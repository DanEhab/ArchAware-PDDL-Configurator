"""
================================================================================
SECTION 12: THREATS TO VALIDITY & LIMITATIONS ANALYSIS
================================================================================
Documents the threats to Internal, External, and Construct validity for the 
Architecture-Aware PDDL Configurator pipeline thesis.

Author: Generated for bachelor thesis analysis
Date: 2026-06-08
================================================================================
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
import textwrap
warnings.filterwarnings('ignore')

# ===== PATHS =====
BASE_DIR = Path(r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator")
OUTPUT_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "12_Threats_Validity"

# Create output directories
(OUTPUT_DIR / "tables").mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 16,
    'axes.labelsize': 12,
    'figure.facecolor': 'white',
})

def render_table_image(df, output_path, title=None, scale=(1.5, 3.5)):
    # Wrap text in DataFrame to prevent collision
    wrapped_df = df.copy()
    for col in wrapped_df.columns:
        wrapped_df[col] = wrapped_df[col].apply(lambda x: "\n".join(textwrap.wrap(str(x), width=35)))
    
    # Calculate row heights based on newlines
    max_lines_per_row = [max(str(val).count('\n') + 1 for val in row) for row in wrapped_df.values]
    total_lines = sum(max_lines_per_row)
    
    fig, ax = plt.subplots(figsize=(max(len(df.columns) * 5.5, 16), max(total_lines * 0.55, 6)))
    ax.axis('off')
    
    # Wrap column labels
    col_labels = ["\n".join(textwrap.wrap(str(c), width=25)) for c in wrapped_df.columns]
    
    table = ax.table(cellText=wrapped_df.values, colLabels=col_labels, loc='center', cellLoc='left', bbox=[0, 0, 1, 0.88])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    
    for j in range(len(wrapped_df.columns)):
        table[0, j].set_facecolor('#2C3E50')
        table[0, j].set_text_props(color='white', fontweight='bold', ha='center')
        
    for i in range(len(wrapped_df)):
        for j in range(len(wrapped_df.columns)):
            table[i+1, j].set_facecolor('#F8F9FA' if i % 2 == 0 else '#FFFFFF')
            table[i+1, j].set_edgecolor('#DDDDDD')
            # Center the first column
            if j == 0:
                table[i+1, j].set_text_props(ha='left', fontweight='bold')
            else:
                table[i+1, j].set_text_props(ha='left')
                
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_t44_internal_validity():
    print("--- Generating Table G-T44: Threats to Internal Validity ---")
    data = [
        {"Threat": "Non-determinism in LLM outputs", "Description": "The same prompt might yield different results if executed multiple times, injecting noise into the baseline comparisons.", "Mitigation": "Enforced a deterministic temperature setting (0.0) across all LLMs to maximize reproducibility."},
        {"Threat": "Planner timeout sensitivity", "Description": "A cutoff of 360 seconds is arbitrary. Planners might solve instances at 361 seconds, skewing coverage gains.", "Mitigation": "Expanded the standard IPC Agile Track cutoff from 300s to 360s (+1 minute) to give a more fair chance for complex tuples, applied consistently across all stages."},
        {"Threat": "Validation pipeline strictness", "Description": "The V4 PDDL semantic validity checks could falsely flag valid optimizations or permit broken syntax, ruining downstream analysis.", "Mitigation": "Utilized a consistent, strictly-typed regex parsing and VAL validation pipeline equally across all stages."},
        {"Threat": "Docker container variability", "Description": "Container startup times and CPU scheduling overhead add noise to the absolute wall-clock runtime measurements.", "Mitigation": "Executed all tests on consistent hardware, treating startup overhead as a uniform constant penalty."}
    ]
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / "tables" / "G_T44_Internal_Validity.csv", index=False)
    render_table_image(df, OUTPUT_DIR / "tables" / "G_T44_Internal_Validity.png", "G-T44: Threats to Internal Validity")
    return df

def generate_t45_external_validity():
    print("--- Generating Table G-T45: Threats to External Validity ---")
    data = [
        {"Threat": "Domain selection bias", "Description": "Testing only 5 domains might not generalize to all possible PDDL structures or real-world industrial planning tasks.", "Mitigation": "Selected diverse IPC benchmark domains featuring differing action complexities, object scaling, and heuristic difficulty."},
        {"Threat": "Planner selection bias", "Description": "Optimizations discovered for 4 specific planners might fail on entirely different planning algorithms.", "Mitigation": "Chosen planners represent distinct architectural paradigms (LAMA/DecStar for heuristic, BFWS for novelty, Madagascar for SAT)."},
        {"Threat": "LLM selection bias", "Description": "Using 4 LLMs risks findings becoming obsolete as new models are released or if models share training biases.", "Mitigation": "Evaluated the absolute State-Of-The-Art across three distinct providers (OpenAI, Anthropic, Google) and an open-weight model (DeepSeek)."},
        {"Threat": "Instance selection bias", "Description": "Using 15 instances per domain might exclude highly complex edge cases where improvements regress.", "Mitigation": "Systematically selected a wide spread of difficulty levels from trivial to structurally complex within each benchmark dataset."}
    ]
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / "tables" / "G_T45_External_Validity.csv", index=False)
    render_table_image(df, OUTPUT_DIR / "tables" / "G_T45_External_Validity.png", "G-T45: Threats to External Validity")
    return df

def generate_t46_construct_validity():
    print("--- Generating Table G-T46: Threats to Construct Validity ---")
    data = [
        {"Threat": "IPC Score limitations", "Description": "The IPC Score aggressively prioritizes runtime speed over plan quality or total action cost, potentially rewarding 'fast but sloppy' plans.", "Mitigation": "Reported and analyzed secondary metrics including Coverage %, PAR10, and mean Plan Cost to provide a holistic view."},
        {"Threat": "Improvement definitions", "Description": "Labeling a configuration as an 'Improvement' based on binary criteria might mask underlying regressions in specific edge instances.", "Mitigation": "Developed and enforced a strict 3-condition formal framework requiring statistical significance, practical magnitude, and neutral/positive coverage."}
    ]
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / "tables" / "G_T46_Construct_Validity.csv", index=False)
    render_table_image(df, OUTPUT_DIR / "tables" / "G_T46_Construct_Validity.png", "G-T46: Threats to Construct Validity")
    return df

def generate_report(t44, t45, t46):
    print("--- Generating Markdown Report ---")
    lines = []
    lines.append("# Section 12: Threats to Validity — Analysis Report")
    lines.append("")
    lines.append("> **Generated:** 2026-06-08")
    lines.append("> **Goal:** To formally document the limitations, assumptions, and threats to the validity of the empirical findings in this thesis.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Introduction")
    lines.append("Any rigorous empirical analysis must confront its methodological limitations. This section breaks down the threats to validity into three distinct categories: **Internal** (experimental control), **External** (generalizability), and **Construct** (metric design). For each threat identified, a concrete mitigation strategy is detailed.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Table G-T44: Threats to Internal Validity")
    lines.append("Internal validity concerns whether the experimental setup itself introduces bias or noise that could compromise the casual inferences made.")
    lines.append("")
    lines.append("![G-T44: Threats to Internal Validity](../tables/G_T44_Internal_Validity.png)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Table G-T45: Threats to External Validity")
    lines.append("External validity concerns whether the conclusions drawn from this specific sample size of domains, planners, and LLMs can generalize to the broader field of automated planning.")
    lines.append("")
    lines.append("![G-T45: Threats to External Validity](../tables/G_T45_External_Validity.png)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Table G-T46: Threats to Construct Validity")
    lines.append("Construct validity concerns whether the metrics chosen (IPC Score, Improvement frameworks) actually measure the phenomena they are intended to represent.")
    lines.append("")
    lines.append("![G-T46: Threats to Construct Validity](../tables/G_T46_Construct_Validity.png)")
    lines.append("")
    
    report_path = OUTPUT_DIR / "Section12_Threats_to_Validity_Report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved to: {report_path}")

def main():
    print("======================================================================")
    print("SECTION 12: THREATS TO VALIDITY")
    print("======================================================================")
    t44 = generate_t44_internal_validity()
    t45 = generate_t45_external_validity()
    t46 = generate_t46_construct_validity()
    generate_report(t44, t45, t46)
    print("======================================================================")

if __name__ == "__main__":
    main()
