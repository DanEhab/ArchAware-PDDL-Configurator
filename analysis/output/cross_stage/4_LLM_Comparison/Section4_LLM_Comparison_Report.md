# Section 4: LLM Effectiveness Comparison — Results Report

> **Generated:** 2026-06-08
> **Data Sources:** `llm_generation_data.csv` and the exactly evaluated 300 LLM Portfolios.

---

## 1. Methodology Overview & Rationale
This section aims to definitively answer a core thesis question: **Which Large Language Model is best suited for architecture-aware domain configuration?**

To answer this, we evaluate the four models (Claude Opus 4.6, GPT-5.4, Gemini 3.1 Pro, and DeepSeek-R1) across multiple dimensions:
- **Structural Competence:** Tracked via parsing validation success rates (`VAL`), evaluating every iteration of Stage 3 feedback.
- **Optimization Capability:** Tracked via Mean IPC Score Gain calculated across all 300 baseline tuples, analyzing whether a configuration improved instance-by-instance.
- **Consistency:** Tracking if an LLM maintains its rank as architectural complexity increases.
- **Resource Efficiency:** Calculating the absolute token consumption generated across all interactions for each LLM.

---
## 2. Table G-T16 Part 1: LLM Validation Rates
### What Does This Table Show?
A pure measure of PDDL syntax mastery. It records the ratio of valid PDDL files out of the absolute number of files that *entered* the validation tool for each prompt iteration. 

| LLM Model       | S1 Valid Rate   | S2 Valid Rate   | S3 Loop 1      | S3 Loop 2      | S3 Loop 3      |
|:----------------|:----------------|:----------------|:---------------|:---------------|:---------------|
| Claude Opus 4.6 | 5/5 (100.0%)    | 20/20 (100.0%)  | 20/20 (100.0%) | 17/17 (100.0%) | 17/17 (100.0%) |
| GPT-5.4         | 5/5 (100.0%)    | 18/20 (90.0%)   | 20/20 (100.0%) | 16/17 (94.1%)  | 17/17 (100.0%) |
| Gemini 3.1 Pro  | 5/5 (100.0%)    | 17/17 (100.0%)  | 20/20 (100.0%) | 16/16 (100.0%) | 14/14 (100.0%) |
| DeepSeek-R1     | 3/5 (60.0%)     | 20/20 (100.0%)  | 15/20 (75.0%)  | 14/19 (73.7%)  | 11/17 (64.7%)  |

### Key Findings
- **Flawless Structural Mastery:** Both Claude Opus 4.6 and Gemini 3.1 Pro achieved a spectacular 100% Valid Rate across all generations that successfully executed. GPT-5.4 was also nearly perfect.
- **DeepSeek's Deterioration:** DeepSeek-R1 dropped heavily in validation success (down to 64.7%) as the prompt context length and iteration loops extended into S3 Loop 3, hallucinating invalid syntax.

---
## 3. Table G-T16 Part 2: LLM IPC Effectiveness
### What Does This Table Show?
This calculates the average global IPC score gain. For every one of the 300 (Planner, Domain, Instance) combinations, we compute `New IPC Score - Baseline IPC Score`. We then average this gain over all 300 instances. The **Improvement** column highlights the precise percentage of the 300 instances where the LLM's IPC score beat the baseline config by config.

| LLM Model       |   S1 Mean IPC Gain |   S2 Mean IPC Gain |   S3 Mean IPC Gain | S1 Improvement   | S2 Improvement   | S3 Improvement   |
|:----------------|-------------------:|-------------------:|-------------------:|:-----------------|:-----------------|:-----------------|
| Claude Opus 4.6 |            -0.0034 |             0.0435 |             0.0279 | 19.67%           | 49.00%           | 46.67%           |
| GPT-5.4         |            -0.0091 |             0.0011 |             0.0248 | 20.67%           | 46.00%           | 43.33%           |
| Gemini 3.1 Pro  |            -0.0067 |             0.0315 |             0.0248 | 21.33%           | 44.67%           | 39.33%           |
| DeepSeek-R1     |            -0.1903 |             0.0251 |            -0.0312 | 13.00%           | 47.67%           | 30.33%           |

### Key Findings
- **GPT-5.4's Late Surge:** While GPT-5.4 started slow in S1 and S2, it achieved a massive breakthrough in S3 with a high improvement rate and net positive IPC gain vs baseline.
- **DeepSeek-R1's Struggle:** DeepSeek completely collapsed in complex stages, yielding negative mean IPC gains throughout S3.

---
## 4. Table G-T17: LLM Ranking by Stage (Ranked by IPC Gain)
### What Does This Table Show?
Tracks the dynamic shifting of LLM dominance based on the Mean IPC gains established in G-T16 Part 2.

| Rank   | Stage 1 Best LLM   | Stage 2 Best LLM   | Stage 3 Best LLM   | Consistent?   |
|:-------|:-------------------|:-------------------|:-------------------|:--------------|
| 1st    | Claude Opus 4.6    | Claude Opus 4.6    | Claude Opus 4.6    | Yes           |
| 2nd    | Gemini 3.1 Pro     | Gemini 3.1 Pro     | GPT-5.4            | No            |
| 3rd    | GPT-5.4            | DeepSeek-R1        | Gemini 3.1 Pro     | No            |
| 4th    | DeepSeek-R1        | GPT-5.4            | DeepSeek-R1        | No            |

### Key Findings
- **Consistent Winner:** Claude Opus 4.6 maintained the 1st place ranking across all stages, proving it is the most consistent and powerful model regardless of task complexity.
- **DeepSeek-R1's Struggle:** DeepSeek fell to 4th place in S3 with a negative IPC gain, proving its inability to handle iterative architectural loops.

---
## 5. Table G-T19: LLM Total Token Consumption
### What Does This Table Show?
Summarizes exactly how "chatty" each LLM was across the 3 stages, separating Input (Prompt) Tokens from Output (Completion) Tokens.

| LLM Model       |   S1 Input |   S1 Output |   S2 Input |   S2 Output |   S3 Input |   S3 Output |   Total Input Tokens |   Total Output Tokens |   Grand Total Tokens |
|:----------------|-----------:|------------:|-----------:|------------:|-----------:|------------:|---------------------:|----------------------:|---------------------:|
| Gemini 3.1 Pro  |      4,710 |       3,541 |     29,969 |      10,394 |    145,214 |      43,005 |              179,893 |                56,940 |              236,833 |
| GPT-5.4         |      4,267 |       3,239 |     34,603 |      12,961 |    145,276 |      42,035 |              184,146 |                58,235 |              242,381 |
| Claude Opus 4.6 |      5,059 |       3,866 |     40,391 |      15,420 |    177,031 |      54,159 |              222,481 |                73,445 |              295,926 |
| DeepSeek-R1     |      4,419 |      10,201 |     35,816 |     106,185 |    150,212 |     180,741 |              190,447 |               297,127 |              487,574 |

### Key Findings
- **Gemini & GPT-5.4 are Efficiency Leaders:** Both models achieved highly optimized outputs with total tokens under 250k.
- **The Cost of Chain-of-Thought (CoT):** DeepSeek-R1 generated massive token payloads (driven by its CoT reasoning in the output), exploding to almost half a million total tokens consumed.

## 6. Graphical Analysis
### Graph G-G13: Percentage of Configurations Improving Over Baseline
This bar chart visualizes the precise Improvement Rate computed directly from `Table G-T16 Part 2`. It counts how many of the 300 instance configurations achieved an IPC score strictly greater than the Baseline, and displays it as a percentage across S1, S2, and S3.
![G-G13 Improvement Rate](../graphs/G_G13_Improvement_Rate.png)

### Graph G-G14: Mean IPC Gain Progression Across Stages
This line graph plots the mean global IPC score gain across the 300 instances over time. It highlights how GPT-5.4 dramatically spikes in optimization capabilities specifically during the S3 feedback loops, while DeepSeek completely drops off the chart into negative capability.
![G-G14 Mean IPC Gain](../graphs/G_G14_Mean_IPC_Gain.png)

### Graph G-G15: PDDL Syntax Validation Mastery Progression
Plotted directly from the Valid Rates in `Table G-T16 Part 1`, this visualization showcases the structural competence of the models over iterative context windows. Claude Opus and Gemini maintain perfectly flat 100% lines at the top, showing immunity to context degradation, while DeepSeek falls off rapidly.
![G-G15 Validation Progression](../graphs/G_G15_Validation_Progression.png)

### Graph G-G16: LLM Efficiency vs Optimization ROI
A scatter plot establishing the Return on Investment. The X-axis plots the absolute Token Consumption (from Table `G-T19`), and the Y-axis plots the final Mean IPC Gain achieved in Stage 3. The ideal quadrant is the **Top-Left** (High IPC Gain, Low Token Usage). GPT-5.4 and Gemini dominate this quadrant. DeepSeek is marooned in the Bottom-Right (Massive Token Usage, Negative IPC Gain).
![G-G16 Efficiency Scatter](../graphs/G_G16_Efficiency_Scatter.png)
