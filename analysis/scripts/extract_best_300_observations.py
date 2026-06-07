import pandas as pd
import numpy as np
from pathlib import Path

# ===== PATHS =====
BASE_DIR = Path(r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator")
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "0_Best_300_Observations_Per_Stage"
MAIN_CSV = RESULTS_DIR / "planner_execution_data.csv"
FB_CSV = RESULTS_DIR / "feedback_loop" / "feedback_loop_planner_execution_data.csv"

# Pre-calculated T* reference files
TSTAR_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "1_Global_IPC_Score (Most Important)" / "tables"

# Mapping logic
LLM_RAW_MAP = {
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "claude-opus-4-6": "Claude Opus 4.6",
    "deepseek-reasoner": "DeepSeek-R1",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1 Pro"
}

def load_all_data():
    # 2) Load Raw Data
    df = pd.read_csv(MAIN_CSV)
    
    # Map LLM names
    df['LLM_Clean'] = df['LLM_Used'].map(lambda x: LLM_RAW_MAP.get(x, x))
    
    # Map stages
    def map_stage(s):
        if s == "BASELINE": return "S0"
        if s == "General": return "S1"
        if s in ["Arch_Aware", "Cross_Test"]: return "S2"
        if s.startswith("Feedback_Loop"): return "S3"
        return "Unknown"
    
    df['Stage_Mapped'] = df['Stage'].apply(map_stage)
    
    # Ensure Runtime_wall_s is numeric and handle missing
    df['Runtime_wall_s'] = pd.to_numeric(df['Runtime_wall_s'], errors='coerce')
    # For sorting, unresolved gets inf runtime
    df['Runtime_Sort'] = df['Runtime_wall_s'].fillna(float('inf'))
    df.loc[df['Output_Status'] != 'SUCCESS', 'Runtime_Sort'] = float('inf')
    
    return df

def calculate_ipc(row):
    tstar = row['T_star']
    if pd.isna(tstar) or str(tstar).strip().upper() == "UNSOLVED":
        return 0.0
    try:
        tstar = float(tstar)
    except ValueError:
        return 0.0
        
    runtime = row['Runtime_wall_s']
    if tstar <= 0 or runtime <= 0 or row['Output_Status'] != 'SUCCESS':
        return 0.0
    ratio = runtime / tstar
    if ratio <= 0:
        return 0.0
    score = 1.0 / (1.0 + np.log10(ratio))
    return max(0.0, min(1.0, score))

def process_context(df_all, context_name):
    print(f"\nProcessing Context: {context_name}")
    tstar_path = TSTAR_DIR / context_name / "T_star_reference.csv"
    tstar_df = pd.read_csv(tstar_path)
    
    # Clean tstar_df
    if 'Planner' in tstar_df.columns:
        tstar_df = tstar_df[['Planner', 'Domain', 'Instance', 'T_star']]
        # Merge T* into the main dataframe
        df = df_all.merge(
            tstar_df,
            left_on=['Planner_Used', 'Domain_Name', 'Problem_Instance'],
            right_on=['Planner', 'Domain', 'Instance'],
            how='left'
        )
        # Drop the duplicate columns from the right side of the merge
        df = df.drop(columns=['Planner', 'Domain', 'Instance'])
    else:
        tstar_df = tstar_df[['Domain', 'Instance', 'T_star']]
        df = df_all.merge(
            tstar_df,
            left_on=['Domain_Name', 'Problem_Instance'],
            right_on=['Domain', 'Instance'],
            how='left'
        )
        df = df.drop(columns=['Domain', 'Instance'])
    
    # Calculate IPC
    df['IPC_Score'] = df.apply(calculate_ipc, axis=1)
    
    # Sort so that the first row in a group is the absolute best
    # Primary: IPC_Score (descending), Secondary: Runtime_Sort (ascending)
    df = df.sort_values(by=['IPC_Score', 'Runtime_Sort'], ascending=[False, True])
    
    # Group by Planner, Domain, Instance, Mapped_Stage
    best_df = df.groupby(['Planner_Used', 'Domain_Name', 'Problem_Instance', 'Stage_Mapped']).head(1).copy()
    
    out_dir = OUTPUT_DIR / context_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Rename common columns
    best_df = best_df.rename(columns={
        'Planner_Used': 'Planner',
        'Domain_Name': 'Domain',
        'Problem_Instance': 'Instance'
    })
    
    # Extract S0
    s0 = best_df[best_df['Stage_Mapped'] == 'S0']
    s0_out = s0[['Planner', 'Domain', 'Instance', 'IPC_Score']]
    s0_out = s0_out.sort_values(by=['Planner', 'Domain', 'Instance'])
    s0_out.to_csv(out_dir / "Stage0_Best_300.csv", index=False)
    print(f"  S0: {len(s0_out)} observations saved.")
    
    # Extract S1
    s1 = best_df[best_df['Stage_Mapped'] == 'S1']
    s1_out = s1[['Planner', 'Domain', 'Instance', 'IPC_Score', 'LLM_Clean']]
    s1_out = s1_out.rename(columns={'LLM_Clean': 'LLM'})
    s1_out = s1_out.sort_values(by=['Planner', 'Domain', 'Instance'])
    s1_out.to_csv(out_dir / "Stage1_Best_300.csv", index=False)
    print(f"  S1: {len(s1_out)} observations saved.")
    
    # Extract S2
    s2 = best_df[best_df['Stage_Mapped'] == 'S2'].copy()
    s2['Prompt_Type'] = s2['Stage']  # Will be 'Arch_Aware' or 'Cross_Test'
    s2_out = s2[['Planner', 'Domain', 'Instance', 'IPC_Score', 'LLM_Clean', 'Prompt_Type', 'PromptID']]
    s2_out = s2_out.rename(columns={'LLM_Clean': 'LLM', 'PromptID': 'Prompt_ID'})
    s2_out = s2_out.sort_values(by=['Planner', 'Domain', 'Instance'])
    s2_out.to_csv(out_dir / "Stage2_Best_300.csv", index=False)
    print(f"  S2: {len(s2_out)} observations saved.")
    
    # Extract S3
    s3 = best_df[best_df['Stage_Mapped'] == 'S3'].copy()
    # Extract iteration number
    s3['Iteration'] = s3['Stage'].str.replace('Feedback_Loop', '')
    s3_out = s3[['Planner', 'Domain', 'Instance', 'IPC_Score', 'LLM_Clean', 'Iteration']]
    s3_out = s3_out.rename(columns={'LLM_Clean': 'LLM'})
    s3_out = s3_out.sort_values(by=['Planner', 'Domain', 'Instance'])
    s3_out.to_csv(out_dir / "Stage3_Best_300.csv", index=False)
    print(f"  S3: {len(s3_out)} observations saved.")

def main():
    print("Loading data...")
    df_all = load_all_data()
    
    # 300 baseline instances expected
    expected = 4 * 5 * 15
    print(f"Total theoretical expected configurations: {expected}")
    
    process_context(df_all, "Configuration_Sensitivity")
    process_context(df_all, "Simulated_Competition")
    
    print(f"\nAll tables have been saved successfully to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
