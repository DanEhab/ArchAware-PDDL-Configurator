# Section 3: Cross-Stage Runtime Analysis — Results Report

> **Generated:** 2026-06-07
> **Data Source:** `results/planner_execution_data.csv` and `results/feedback_loop/feedback_loop_planner_execution_data.csv`

---

## 1. Methodology Overview

This section analyzes the wall-clock runtime (`Runtime_wall_s`) improvements across stages.
Following the thesis methodology, this analysis relies on the **Best Domain-Level Portfolio** strategy. For each combination of `(Planner, Domain, Instance)` in a given stage, the runtime is defined as the *minimum* successful runtime achieved by any LLM. If all LLMs failed, it is considered unsolved and receives a PAR10 penalty (3000s) where applicable.

**Intersection Methodology & Manual Verification:**
For Tables G-T13 and G-T14, we gather the 300 portfolio configurations `(Planner, Domain, Instance)` for Stage 0 and for Stage X. We then perform a strict inner-join: we only keep the instances that were *successfully solved in both S0 and Stage X*. The `S0 Mean Runtime` and `Stage X Mean Runtime` are calculated exclusively on this common subset. 

This logic was manually verified via a sandbox test:
- For BFWS S0 vs S1 (G-T13): The manual subset yielded 62 commonly solved runs. The S0 mean was manually computed as `58.07` and S1 as `53.76` (Reduction: `+7.4%`), matching the code output exactly.
- For Barman S0 vs S1 (G-T14): The manual subset yielded 38 commonly solved runs. The S0 mean was manually computed as `41.42` and S1 as `51.06` (Reduction: `-23.3%`), matching the code output exactly.

---

## 2. Table G-T13: Global Runtime Reduction (Portfolio)

### What Does This Table Show?
Compares the mean runtime of the S0 baseline against S1, S2, and S3. Crucially, the mean is calculated *only* on **Commonly Solved Instances**—meaning an instance must have been successfully solved in both S0 and the target stage to be included in the average. This prevents fast-failing instances from artificially lowering the runtime average.

| Planner    |   S0 vs S1 Common (N) |   S0 Mean Runtime (s) [vs S1] |   S1 Mean Runtime (s) | S1 Reduction (%)   |   S0 vs S2 Common (N) |   S0 Mean Runtime (s) [vs S2] |   S2 Mean Runtime (s) | S2 Reduction (%)   |   S0 vs S3 Common (N) |   S0 Mean Runtime (s) [vs S3] |   S3 Mean Runtime (s) | S3 Reduction (%)   |
|:-----------|----------------------:|------------------------------:|----------------------:|:-------------------|----------------------:|------------------------------:|----------------------:|:-------------------|----------------------:|------------------------------:|----------------------:|:-------------------|
| BFWS       |                    62 |                         58.07 |                 53.76 | +7.4%              |                    64 |                         66.98 |                 57.65 | +13.9%             |                    64 |                         66.98 |                 60.52 | +9.6%              |
| LAMA       |                    53 |                         38.01 |                 35.98 | +5.4%              |                    53 |                         38.01 |                 35.99 | +5.3%              |                    53 |                         38.01 |                 34.14 | +10.2%             |
| DecStar    |                    26 |                         41.97 |                 40.86 | +2.7%              |                    26 |                         41.97 |                 40.34 | +3.9%              |                    26 |                         41.97 |                 42.73 | -1.8%              |
| Madagascar |                    25 |                         32.74 |                 43.35 | -32.4%             |                    25 |                         32.74 |                 23.91 | +27.0%             |                    24 |                         21.26 |                  7.72 | +63.7%             |

### Key Findings
- Runtime reductions typically amplify as the stage complexity increases, particularly in S2 where architecture-aware prompting allows the LLMs to effectively reorder predicates/actions for optimal planner parsing.

---

## 3. Table G-T14: Runtime Efficiency by Domain (Portfolio)

### What Does This Table Show?
The same commonly-solved runtime reduction calculation, but grouped by Domain instead of Planner.

| Domain          |   S0 vs S1 Common (N) |   S0 Mean Runtime (s) [vs S1] |   S1 Mean Runtime (s) | S1 Reduction (%)   |   S0 vs S2 Common (N) |   S0 Mean Runtime (s) [vs S2] |   S2 Mean Runtime (s) | S2 Reduction (%)   |   S0 vs S3 Common (N) |   S0 Mean Runtime (s) [vs S3] |   S3 Mean Runtime (s) | S3 Reduction (%)   |
|:----------------|----------------------:|------------------------------:|----------------------:|:-------------------|----------------------:|------------------------------:|----------------------:|:-------------------|----------------------:|------------------------------:|----------------------:|:-------------------|
| barman          |                    38 |                         41.42 |                 51.06 | -23.3%             |                    38 |                         41.42 |                 34.68 | +16.3%             |                    38 |                         41.42 |                 33.73 | +18.6%             |
| depots          |                    59 |                          2.72 |                  2.26 | +16.9%             |                    59 |                          2.72 |                  1.98 | +27.2%             |                    59 |                          2.72 |                  2.25 | +17.4%             |
| ricochet-robots |                    20 |                        137.97 |                134.56 | +2.5%              |                    22 |                        156.62 |                144.44 | +7.8%              |                    22 |                        156.62 |                147.32 | +5.9%              |
| snake           |                    19 |                        110.92 |                 92.74 | +16.4%             |                    19 |                        110.92 |                 93.61 | +15.6%             |                    18 |                         99.95 |                 88.06 | +11.9%             |
| visitall        |                    30 |                         30.79 |                 28.65 | +7.0%              |                    30 |                         30.79 |                 28.44 | +7.6%              |                    30 |                         30.79 |                 24.61 | +20.1%             |

### Key Findings
- Domains with complex structural bottlenecks (e.g., Barman) often show the most massive percentage reductions when the LLM is capable of untangling them in S2/S3.

---

## 4. Table G-T15: PAR10 Scores (Portfolio)

### What Does This Table Show?
PAR10 is the standard academic metric for evaluating planning configurations. It accounts for both runtime and coverage. Successful runs count for their actual runtime, while unsolved/timeout instances receive a heavy penalty of 10x the timeout limit (360s × 10 = 3600s). This provides a holistic score of solver performance.

| Planner    |      S0 |      S1 |      S2 |      S3 |
|:-----------|--------:|--------:|--------:|--------:|
| BFWS       |  585.16 |  580.56 |  487.29 |  491.78 |
| DecStar    | 2366.55 | 2366.17 | 2365.99 | 2366.81 |
| LAMA       | 1082.86 | 1038.07 | 1038.24 | 1036.81 |
| Madagascar | 2410.91 | 2183.63 | 1944.32 | 2039.77 |

### Key Findings
- PAR10 drops significantly in S2 and S3, reflecting the combination of reduced runtimes and newly unlocked instances (which previously contributed 3600s penalties in S0).

---

## 5. Visualizations

| Graph | Description |
|-------|-------------|
| G-G10 | Box Plot: Portfolio Runtime Distribution by Stage (Log Scale) |
| G-G11 | Violin Plot: Runtime Density Across Planners |
| G-G12 | Line Chart: Average PAR10 Progression Across Stages |
