import pandas as pd

df = pd.read_csv(r'c:\Users\danie\My Drive\ArchAware-PDDL-Configurator\results\planner_execution_data.csv')

# Check what PromptID maps to which planner in Arch_Aware
aa = df[df['Stage']=='Arch_Aware']
for pid in sorted(aa['PromptID'].dropna().unique()):
    planners = aa[aa['PromptID']==pid]['Planner_Used'].unique()
    print("PromptID {}: Planners = {}".format(int(pid), planners))

# Check Stage 1 General
gen = df[df['Stage']=='General']
print("\nGeneral: LLMs =", gen["LLM_Used"].unique())
print("General: PromptID =", gen["PromptID"].unique())
print("General rows:", len(gen))

# Feedback Loop stages
for s in ['Feedback_Loop1','Feedback_Loop2','Feedback_Loop3']:
    fb = df[df['Stage']==s]
    print("\n{}: rows={}, LLMs={}, Planners={}".format(s, len(fb), fb["LLM_Used"].nunique(), fb["Planner_Used"].unique()))

# Check the separate feedback loop CSV
fb_csv = pd.read_csv(r'c:\Users\danie\My Drive\ArchAware-PDDL-Configurator\results\feedback_loop\feedback_loop_planner_execution_data.csv')
print("\n=== Feedback Loop separate CSV ===")
print("Columns:", list(fb_csv.columns))
print("Rows:", len(fb_csv))
print("Stages:", fb_csv['Stage'].unique() if 'Stage' in fb_csv.columns else "No Stage column")

# Iteration tracking
it = pd.read_csv(r'c:\Users\danie\My Drive\ArchAware-PDDL-Configurator\results\feedback_loop\iteration_tracking.csv')
print("\n=== Iteration Tracking ===")
print("Columns:", list(it.columns))
print("Rows:", len(it))
print("Unique (domain, llm, planner):", it.groupby(['Domain','LLM','Planner']).ngroups)
print("Iteration values:", sorted(it['Iteration'].unique()))
print("Status values:", it['Validation_Status'].value_counts().to_dict())

# Check unique instances
for dom in sorted(df['Domain_Name'].unique()):
    instances = sorted(df[df['Domain_Name']==dom]['Problem_Instance'].unique())
    print("\n{}: {} instances".format(dom, len(instances)))

# Cross_Test stage
ct = df[df['Stage']=='Cross_Test']
print("\n=== Cross_Test ===")
print("Rows:", len(ct))
print("Unique combos (Domain,LLM,PromptID,Planner):", ct.groupby(['Domain_Name','LLM_Used','PromptID','Planner_Used']).ngroups)
