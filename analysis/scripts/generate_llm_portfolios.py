import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator")
MAIN_CSV = BASE_DIR / "results" / "planner_execution_data.csv"
OUTPUT_DIR = BASE_DIR / "analysis" / "output" / "cross_stage" / "4_LLM_Comparison" / "LLM_Portfolios"

LLM_MAP = {
    "claude-opus-4-6": "Claude Opus 4.6",
    "gpt-5.4-2026-03-05": "GPT-5.4",
    "gemini-3.1-pro-preview-customtools": "Gemini 3.1 Pro",
    "deepseek-reasoner": "DeepSeek-R1"
}

PLANNERS = ["bfws", "lama", "decstar", "madagascar"]
DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
INSTANCES = ['instance-01.pddl', 'instance-02.pddl', 'instance-03.pddl',
             'instance-04.pddl', 'instance-07.pddl', 'instance-08.pddl',
             'instance-09.pddl', 'instance-11.pddl', 'instance-12.pddl',
             'instance-13.pddl', 'instance-14.pddl', 'instance-16.pddl',
             'instance-17.pddl', 'instance-18.pddl', 'instance-19.pddl']

def main():
    print("Loading data...")
    df = pd.read_csv(MAIN_CSV)
    
    # Pre-process
    df['LLM_Mapped'] = df['LLM_Used'].map(lambda x: LLM_MAP.get(x, x))
    df['Is_Solved'] = (df['Output_Status'] == 'SUCCESS').astype(int)
    
    # Calculate T* (global minimum runtime per Planner, Domain, Instance for SUCCESS runs)
    success_df = df[df['Is_Solved'] == 1]
    t_star = success_df.groupby(['Planner_Used', 'Domain_Name', 'Problem_Instance'])['Runtime_wall_s'].min().reset_index()
    t_star = t_star.rename(columns={'Runtime_wall_s': 'T_star'})
    
    # Merge T* back into main dataframe
    df = pd.merge(df, t_star, on=['Planner_Used', 'Domain_Name', 'Problem_Instance'], how='left')
    
    # Calculate IPC Score using 1 / (1 + log10(T / T*))
    df['IPC Score'] = np.where(
        df['Is_Solved'] == 1, 
        1.0 / (1.0 + np.log10(df['Runtime_wall_s'] / df['T_star'])), 
        0.0
    )
    
    # Format floats properly so they aren't massive decimals
    def format_ipc(val):
        if pd.isna(val) or val == 'N/A':
            return 'N/A'
        return round(val, 4)

    # Create base dataframe of the 300 portfolios
    base_rows = []
    for p in PLANNERS:
        for d in DOMAINS:
            for i in INSTANCES:
                base_rows.append({'Planner_Used': p, 'Domain_Name': d, 'Problem_Instance': i})
    base_df = pd.DataFrame(base_rows)
    
    for llm in LLM_MAP.values():
        llm_dir = OUTPUT_DIR / llm
        llm_dir.mkdir(parents=True, exist_ok=True)
        print(f"Generating portfolios for {llm}...")
        
        # S1
        s1_df = df[(df['LLM_Mapped'] == llm) & (df['Stage'] == 'General')]
        s1_df = s1_df.sort_values(by=['IPC Score', 'Runtime_wall_s'], ascending=[False, True]).drop_duplicates(subset=['Planner_Used', 'Domain_Name', 'Problem_Instance'])
        s1_merged = pd.merge(base_df, s1_df[['Planner_Used', 'Domain_Name', 'Problem_Instance', 'IPC Score']], on=['Planner_Used', 'Domain_Name', 'Problem_Instance'], how='left')
        s1_merged['IPC Score'] = s1_merged['IPC Score'].fillna('N/A').apply(lambda x: format_ipc(x) if x != 'N/A' else x)
        s1_merged.rename(columns={'Planner_Used': 'Planner', 'Domain_Name': 'Domain', 'Problem_Instance': 'Instance'}, inplace=True)
        s1_merged.to_csv(llm_dir / "S1.csv", index=False)
        
        # S2
        s2_df = df[(df['LLM_Mapped'] == llm) & (df['Stage'].isin(['Arch_Aware', 'Cross_Test']))]
        s2_df = s2_df.sort_values(by=['IPC Score', 'Runtime_wall_s'], ascending=[False, True]).drop_duplicates(subset=['Planner_Used', 'Domain_Name', 'Problem_Instance'])
        s2_merged = pd.merge(base_df, s2_df[['Planner_Used', 'Domain_Name', 'Problem_Instance', 'IPC Score', 'Stage', 'PromptID']], on=['Planner_Used', 'Domain_Name', 'Problem_Instance'], how='left')
        s2_merged['IPC Score'] = s2_merged['IPC Score'].fillna('N/A').apply(lambda x: format_ipc(x) if x != 'N/A' else x)
        s2_merged['Stage'] = s2_merged['Stage'].fillna('N/A')
        s2_merged['PromptID'] = s2_merged['PromptID'].fillna('N/A')
        s2_merged.rename(columns={'Planner_Used': 'Planner', 'Domain_Name': 'Domain', 'Problem_Instance': 'Instance', 'PromptID': 'Prompt ID'}, inplace=True)
        s2_merged.to_csv(llm_dir / "S2.csv", index=False)
        
        # S3
        s3_df = df[(df['LLM_Mapped'] == llm) & (df['Stage'].str.startswith('Feedback_Loop', na=False))]
        s3_df['Iteration'] = s3_df['Stage'].str.replace('Feedback_Loop', '')
        s3_df = s3_df.sort_values(by=['IPC Score', 'Runtime_wall_s'], ascending=[False, True]).drop_duplicates(subset=['Planner_Used', 'Domain_Name', 'Problem_Instance'])
        s3_merged = pd.merge(base_df, s3_df[['Planner_Used', 'Domain_Name', 'Problem_Instance', 'IPC Score', 'Stage', 'PromptID', 'Iteration']], on=['Planner_Used', 'Domain_Name', 'Problem_Instance'], how='left')
        s3_merged['IPC Score'] = s3_merged['IPC Score'].fillna('N/A').apply(lambda x: format_ipc(x) if x != 'N/A' else x)
        s3_merged['Stage'] = s3_merged['Stage'].fillna('N/A')
        s3_merged['PromptID'] = s3_merged['PromptID'].fillna('N/A')
        s3_merged['Iteration'] = s3_merged['Iteration'].fillna('N/A')
        s3_merged.rename(columns={'Planner_Used': 'Planner', 'Domain_Name': 'Domain', 'Problem_Instance': 'Instance', 'PromptID': 'Prompt ID'}, inplace=True)
        s3_merged.to_csv(llm_dir / "S3.csv", index=False)
        
    print("All 12 files successfully generated.")

if __name__ == '__main__':
    main()
