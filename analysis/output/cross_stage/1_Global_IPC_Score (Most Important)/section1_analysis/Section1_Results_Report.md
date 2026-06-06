# Section 1: Global IPC Score Analysis — Results Report

> **Generated:** 2026-06-06  
> **Context:** Cross-Stage Comparative Analysis  
> **Data Source:** Pre-calculated global IPC scores from `1_Global_IPC_Score (Most Important)/tables/`

---

## Methodological Note: Method 2 (Domain-Level Portfolio)
> **Note:** For the `(best)` columns in Stage 1 and Stage 2 (and the Mean Gain tables G-T6 and G-T7), this analysis uses **Method 2 (The Best Domain-Level Portfolio)**.
> Instead of selecting a single best LLM overall, it calculates the theoretical maximum by taking the best score achieved by *any* LLM for each specific domain, and summing those up. This ensures a true apples-to-apples comparison with Stage 3 (Feedback Loop), which also uses a portfolio/best-iteration approach. It creates a strict ablation study, neutralizing the confounding variable of 'number of attempts', and evaluates the pure theoretical maximum of each prompting strategy.

## Table G-T1: Global IPC Score — Per Stage x Per Planner

### Configuration Sensitivity

| Planner    |   S0 IPC |   S1 IPC (avg) |   S1 IPC (best) | S1 Best LLM   |   S2 IPC (avg) |   S2 IPC (best) |   S3 IPC (best) | Best Stage   |   Δ Best vs S0 |
|:-----------|---------:|---------------:|----------------:|:--------------|---------------:|----------------:|----------------:|:-------------|---------------:|
| BFWS       |  58.11   |        50.6073 |         59.0036 | Portfolio     |        54.3984 |         60.6837 |         62.643  | S3           |         4.533  |
| LAMA       |  49.9257 |        44.9347 |         51.2872 | Portfolio     |        45.9516 |         51.6126 |         52.9656 | S3           |         3.0399 |
| DecStar    |  25.1264 |        22.7351 |         25.1816 | Portfolio     |        21.169  |         25.8374 |         25.1461 | S2           |         0.711  |
| Madagascar |  21.0067 |        20.1808 |         22.4575 | Portfolio     |        21.6474 |         23.3036 |         23.118  | S2           |         2.2969 |
| **TOTAL**  | 154.169  |       138.458  |        157.93   | —             |       143.166  |        161.437  |        163.873  | S3           |         9.7039 |

### Simulated Competition

| Planner    |   S0 IPC |   S1 IPC (avg) |   S1 IPC (best) | S1 Best LLM   |   S2 IPC (avg) |   S2 IPC (best) |   S3 IPC (best) | Best Stage   |   Δ Best vs S0 |
|:-----------|---------:|---------------:|----------------:|:--------------|---------------:|----------------:|----------------:|:-------------|---------------:|
| BFWS       |  46.0822 |        40.4626 |         46.3553 | Portfolio     |        42.807  |         47.8356 |         49.8311 | S3           |         3.7489 |
| LAMA       |  40.3947 |        35.5696 |         41.0668 | Portfolio     |        36.3271 |         41.5144 |         42.095  | S3           |         1.7003 |
| DecStar    |  17.2045 |        15.3629 |         17.2266 | Portfolio     |        14.7252 |         17.551  |         17.2055 | S2           |         0.3465 |
| Madagascar |  19.9944 |        19.4474 |         21.5246 | Portfolio     |        20.8076 |         22.1483 |         21.226  | S2           |         2.1539 |
| **TOTAL**  | 123.676  |       110.843  |        126.173  | —             |       114.667  |        129.049  |        130.358  | S3           |         6.6818 |

---

## Table G-T4: Simulated Competition IPC Scores Per Stage

> **Methodological Note on Stage Scoring:**
> To calculate the 'Total IPC' for Stage 1, Stage 2, and Stage 3 in the Simulated Competition context, the script evaluates performance on a **per-instance portfolio basis**:
> 1. **Group by Unique Triples**: The execution data is grouped by unique combinations of `(Planner, Domain, Instance)`, totaling 300 instances (4 planners × 5 domains × 15 instances).
> 2. **Evaluate all Candidates**: For each specific triple (e.g., `BFWS`, `barman`, `instance_1`), multiple PDDL models were generated (e.g., 4 models in Stage 1, one from each LLM; or 5 iterations in Stage 3).
> 3. **Take the Maximum**: Because this is a 'Simulated Competition' (where the competition framework takes the best result from all submissions), the script selects the `max()` IPC score out of those candidate LLMs/iterations for that specific instance.
> 4. **Sum the 300 Bests**: Finally, it adds up these 300 'best' per-instance scores to yield the Total IPC for the Stage.

| Stage                         |   Instances (n) |   Total IPC |   Mean IPC |   Median IPC |   % Score > 0 |
|:------------------------------|----------------:|------------:|-----------:|-------------:|--------------:|
| Stage 0 (Baseline)            |             300 |     123.676 |     0.4123 |       0.4365 |          56   |
| Stage 1 (General, best LLM)   |             300 |     129.47  |     0.4316 |       0.463  |          58   |
| Stage 2 (Arch-Aware, target)  |             300 |     134.707 |     0.449  |       0.468  |          58.3 |
| Stage 3 (Feedback Loop, best) |             300 |     136.086 |     0.4536 |       0.4899 |          59.7 |

---

## Table G-T5: Best Configuration Per Instance (Simulated Competition)

> This is a **headline result** — it directly answers 'Did our approach beat the baseline?'

| Source of Best Performance   |   Count |   out of | Percentage   |
|:-----------------------------|--------:|---------:|:-------------|
| Unsolvable                   |     117 |      300 | 39.0%        |
| Stage 0 (Baseline)           |       3 |      300 | 1.0%         |
| Stage 1 (General Prompt)     |      14 |      300 | 4.7%         |
| Stage 2 (Arch-Aware)         |      52 |      300 | 17.3%        |
| Stage 2 (Cross Test)         |      46 |      300 | 15.3%        |
| Stage 3 (Feedback Loop)      |      68 |      300 | 22.7%        |

---

## Table G-T6: IPC Gain vs. Baseline (Per Planner)

### Configuration Sensitivity

| Planner     |   S1 Gain vs S0 |   S2 Gain vs S0 |   S3 Gain vs S0 | Progressive?   |
|:------------|----------------:|----------------:|----------------:|:---------------|
| BFWS        |          0.8936 |          2.5737 |          4.533  | Yes            |
| LAMA        |          1.3615 |          1.6869 |          3.0399 | Yes            |
| DecStar     |          0.0552 |          0.711  |          0.0197 | No             |
| Madagascar  |          1.4508 |          2.2969 |          2.1113 | No             |
| **Overall** |          3.7611 |          7.2685 |          9.7039 | Yes            |

### Simulated Competition

| Planner     |   S1 Gain vs S0 |   S2 Gain vs S0 |   S3 Gain vs S0 | Progressive?   |
|:------------|----------------:|----------------:|----------------:|:---------------|
| BFWS        |          0.2731 |          1.7534 |          3.7489 | Yes            |
| LAMA        |          0.6721 |          1.1197 |          1.7003 | Yes            |
| DecStar     |          0.0221 |          0.3465 |          0.001  | No             |
| Madagascar  |          1.5302 |          2.1539 |          1.2316 | No             |
| **Overall** |          2.4975 |          5.3735 |          6.6818 | Yes            |

---

## Table G-T7: IPC Gain vs. Baseline (Per Domain)

### Configuration Sensitivity

| Domain          |   S1 Gain vs S0 |   S2 Gain vs S0 |   S3 Gain vs S0 | Progressive?   |
|:----------------|----------------:|----------------:|----------------:|:---------------|
| barman          |          0.8618 |          1.1959 |          2.7902 | Yes            |
| depots          |          0.0549 |          3.7167 |          1.5223 | No             |
| ricochet-robots |          0.6314 |          0.3628 |          2.9803 | No             |
| snake           |          2.0219 |          1.3903 |          0.3868 | No             |
| visitall        |          0.1911 |          0.6028 |          2.0243 | Yes            |

### Simulated Competition

| Domain          |   S1 Gain vs S0 |   S2 Gain vs S0 |   S3 Gain vs S0 | Progressive?   |
|:----------------|----------------:|----------------:|----------------:|:---------------|
| barman          |          0.5656 |          0.6962 |          1.4786 | Yes            |
| depots          |         -0.0574 |          2.7591 |          1.0257 | No             |
| ricochet-robots |          0.1376 |          0.3009 |          2.3629 | Yes            |
| snake           |          1.7499 |          1.1686 |          0.3434 | No             |
| visitall        |          0.1018 |          0.4487 |          1.4712 | Yes            |

---

## Output Files

### Tables (CSV + PNG)
All tables are saved in `section1_analysis/tables/`

### Graphs
All graphs are saved in `section1_analysis/graphs/`
