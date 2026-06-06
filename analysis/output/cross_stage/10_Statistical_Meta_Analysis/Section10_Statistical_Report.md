# Section 10: Statistical Meta-Analysis — Results Report

> **Generated:** 2026-06-06  
> **IPC Context:** Configuration Sensitivity  
> **Data Source:** Per-instance IPC scores computed from `results/planner_execution_data.csv`  
> **Reference:** T* values from `1_Global_IPC_Score (Most Important)/tables/`

---

## Methodology Overview

### Why Non-Parametric Tests?
IPC score distributions are typically **non-normal** (bounded between 0 and 1, with a large mass at 0 for unsolved instances). The Shapiro-Wilk tests (Table G-T33) confirm this. Therefore, all primary statistical tests used in this analysis are **non-parametric**, following the methodology established by Elis's thesis and standard practice in the AI planning community.

### Test Suite
| Test | Purpose | When Used |
|------|---------|-----------|
| **Shapiro-Wilk** | Tests whether data follows a normal distribution | Pre-test: determines if parametric tests are appropriate |
| **Wilcoxon Signed-Rank** | Tests whether two paired samples differ significantly | Pairwise stage comparisons (e.g., S0 vs S1) |
| **Friedman** | Tests whether k related samples differ significantly | Overall comparison across all 4 stages simultaneously |
| **Nemenyi Post-Hoc** | Identifies which specific pairs differ after a significant Friedman test | Follow-up to Friedman test |
| **Cliff's Delta** | Measures the magnitude of difference between two groups (effect size) | All pairwise comparisons — answers 'how big is the difference?' |
| **Kruskal-Wallis** | Tests whether k independent samples differ significantly | Factor analysis (LLM, Planner, Domain effects) |

### Multiple Comparisons Correction
For the 6 pairwise Wilcoxon tests, we apply **Bonferroni correction**: α_adjusted = 0.05 / 6 = **0.0083**. A result is considered statistically significant only if p < 0.0083.

### Effect Size Interpretation (Cliff's Delta)
Following Romano et al. (2006):
| |δ| Range | Interpretation |
|-----------|----------------|
| < 0.147 | Negligible |
| 0.147–0.33 | Small |
| 0.33–0.474 | Medium |
| ≥ 0.474 | Large |

### Data Structure
Each test operates on **300 matched observations** (4 planners × 5 domains × 15 instances). For each observation, the IPC score is the **best score** achieved across all LLMs/iterations within that stage (Method 2: Domain-Level Portfolio), ensuring consistency with Section 1.

---

## Table G-T33: Shapiro-Wilk Normality Test Results

> The Shapiro-Wilk test evaluates whether the IPC score distributions follow a normal (Gaussian) distribution. If p < 0.05, we reject the null hypothesis of normality, justifying the use of non-parametric statistical tests.

| Distribution        |   n |   W statistic |   p-value | Normal? (α=0.05)   |
|:--------------------|----:|--------------:|----------:|:-------------------|
| S0 IPC Scores       | 300 |      0.689644 |  3.83e-23 | No                 |
| S1 IPC Scores       | 300 |      0.684536 |  2.61e-23 | No                 |
| S2 IPC Scores       | 300 |      0.647088 |  1.83e-24 | No                 |
| S3 IPC Scores       | 300 |      0.664549 |  6.14e-24 | No                 |
| IPC Gain (S1 vs S0) | 300 |      0.378748 |  9.56e-31 | No                 |
| IPC Gain (S2 vs S0) | 300 |      0.406274 |  3.25e-30 | No                 |
| IPC Gain (S3 vs S0) | 300 |      0.420201 |  6.14e-30 | No                 |

> **Conclusion:** All distributions are **significantly non-normal** (p < 0.05), confirming that non-parametric tests are the appropriate choice for this analysis.

---

## Table G-T34: Wilcoxon Signed-Rank Test — Pairwise Stage Comparisons

> The Wilcoxon signed-rank test is the non-parametric equivalent of a paired t-test. It tests whether the median difference between two paired samples is significantly different from zero. Bonferroni-corrected α = 0.0083.

| Comparison   |   n (non-zero diffs) |   W statistic |   p-value |   Effect Size (r) | Significant (p<0.0083)?   | Direction     |
|:-------------|---------------------:|--------------:|----------:|------------------:|:--------------------------|:--------------|
| S0 vs S1     |                  176 |        4305   |  2.67e-07 |            0.3879 | Yes                       | No difference |
| S0 vs S2     |                  181 |         262   |  1.37e-29 |          inf      | Yes                       | S2 > S0       |
| S0 vs S3     |                  180 |         729   |  3.19e-26 |          inf      | Yes                       | S3 > S0       |
| S1 vs S2     |                  182 |        1569   |  2.21e-21 |          inf      | Yes                       | S2 > S1       |
| S1 vs S3     |                  180 |        2438.5 |  3.59e-16 |            0.6057 | Yes                       | No difference |
| S2 vs S3     |                  183 |        6230.5 |  0.0023   |            0.2254 | Yes                       | No difference |

---

## Table G-T35: Friedman Test — Overall Stage Differences

> The Friedman test is a non-parametric alternative to repeated-measures ANOVA. It tests whether there are statistically significant differences across all four stages simultaneously. Kendall's W measures the degree of agreement in rankings (0 = no agreement, 1 = complete agreement).

| Factor              | Metric            |       χ² |   p-value |   Kendall's W | Significant (p<0.05)?   |
|:--------------------|:------------------|---------:|----------:|--------------:|:------------------------|
| Stage (S0/S1/S2/S3) | IPC Score         | 267.058  |  1.34e-57 |        0.2967 | Yes                     |
| Stage (S0/S1/S2/S3) | Coverage (binary) |  20.8966 |  0.000111 |        0.0232 | Yes                     |

---

## Table G-T36: Nemenyi Post-Hoc Test

> When the Friedman test is significant, the Nemenyi post-hoc test identifies which specific pairs of stages differ significantly. Two stages are significantly different if their mean rank difference exceeds the Critical Difference (CD).

| Pair     |   Mean Rank (S0) |   Mean Rank (S1) |   Rank Difference |   Critical Difference | Significant?   |   Mean Rank (S2) |   Mean Rank (S3) |
|:---------|-----------------:|-----------------:|------------------:|----------------------:|:---------------|-----------------:|-----------------:|
| S0 vs S1 |           1.9017 |             2.18 |            0.2783 |                0.2708 | Yes            |           nan    |         nan      |
| S0 vs S2 |           1.9017 |           nan    |            1.1383 |                0.2708 | Yes            |             3.04 |         nan      |
| S0 vs S3 |           1.9017 |           nan    |            0.9767 |                0.2708 | Yes            |           nan    |           2.8783 |
| S1 vs S2 |         nan      |             2.18 |            0.86   |                0.2708 | Yes            |             3.04 |         nan      |
| S1 vs S3 |         nan      |             2.18 |            0.6983 |                0.2708 | Yes            |           nan    |           2.8783 |
| S2 vs S3 |         nan      |           nan    |            0.1617 |                0.2708 | No             |             3.04 |           2.8783 |

---

## Table G-T37: Cliff's Delta Effect Sizes

> While statistical significance tells us *whether* a difference exists, effect size tells us *how large* that difference is. Cliff's Delta is a robust, non-parametric effect size measure that quantifies the probability that a randomly selected value from one group is larger than a randomly selected value from another group.

| Comparison   |   Cliff's Delta | Interpretation   | 95% CI             |
|:-------------|----------------:|:-----------------|:-------------------|
| S0 vs S1     |          0.0812 | Negligible       | [0.0024, 0.1671]   |
| S0 vs S2     |          0.3012 | Small            | [0.2185, 0.3859]   |
| S0 vs S3     |          0.2318 | Small            | [0.1473, 0.3171]   |
| S1 vs S2     |          0.2458 | Small            | [0.1610, 0.3317]   |
| S1 vs S3     |          0.1657 | Small            | [0.0793, 0.2484]   |
| S2 vs S3     |         -0.0851 | Negligible       | [-0.1711, -0.0014] |

---

## Table G-T38: Kruskal-Wallis Test — LLM Effect on IPC Score

> The Kruskal-Wallis test is a non-parametric one-way ANOVA. Here it tests whether the choice of LLM significantly affects IPC scores within each stage. A significant result means at least one LLM performs differently from the others.

| Stage   |   H statistic |   p-value | Significant (p<0.05)?   | Best LLM (mean)   | Worst LLM (mean)   |
|:--------|--------------:|----------:|:------------------------|:------------------|:-------------------|
| S1      |        0.043  |   0.998   | No                      | DeepSeek-R1       | GPT-5.4            |
| S2      |       12.0495 |   0.00722 | Yes                     | DeepSeek-R1       | Gemini 3.1 Pro     |
| S3      |        8.2948 |   0.0403  | Yes                     | Gemini 3.1 Pro    | GPT-5.4            |

---

## Table G-T39: Kruskal-Wallis Test — Planner Effect on IPC Gain

> Tests whether the choice of planner significantly affects the IPC gain achieved by LLM-based domain configuration. A significant result means some planners are more 'responsive' to domain reordering than others.

| Stage   |   H statistic |   p-value | Significant (p<0.05)?   | Best Planner   | Worst Planner   |
|:--------|--------------:|----------:|:------------------------|:---------------|:----------------|
| S1      |       26.569  |  7.25e-06 | Yes                     | Madagascar     | DecStar         |
| S2      |       39.9034 |  1.12e-08 | Yes                     | Madagascar     | DecStar         |
| S3      |       76.7212 |  1.55e-16 | Yes                     | Madagascar     | DecStar         |

---

## Table G-T40: Kruskal-Wallis Test — Domain Effect on IPC Gain

> Tests whether the choice of domain significantly affects the IPC gain. A significant result means some domains are inherently more 'optimizable' through domain reordering than others.

| Stage   |   H statistic |   p-value | Significant (p<0.05)?   | Most Responsive Domain   | Least Responsive Domain   |
|:--------|--------------:|----------:|:------------------------|:-------------------------|:--------------------------|
| S1      |       10.6377 |  0.031    | Yes                     | Snake                    | Depots                    |
| S2      |       85.898  |  9.78e-18 | Yes                     | Barman                   | Visitall                  |
| S3      |       34.5563 |  5.73e-07 | Yes                     | Barman                   | Visitall                  |

---

## Graphs

All graphs are saved in `graphs/`:

| Graph | Description |
|-------|-------------|
| G-G28 | KDE overlay of IPC gain distributions by stage |
| G-G29 | Box plot of IPC gains with Wilcoxon significance markers |
| G-G30 | Forest plot of Cliff's Delta effect sizes with 95% CIs |
| G-G31 | Violin plot of IPC score distributions by stage |
