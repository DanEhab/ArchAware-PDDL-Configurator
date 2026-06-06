# IPC Score Methodology & Global T* Reference Report

> **Project:** Architecture-Aware Domain Model Configuration  
> **Date Generated:** 2026-06-05  
> **Data Source:** `results/planner_execution_data.csv` (7,350 rows across 7 stages)

---

## 1. The IPC Score Formula

We use the **IPC Agile Track Score** formula as defined by the International Planning Competition (IPC). This is the same formula used in IPC competitions for evaluating planner speed.

### Formula

For a single problem instance p:

```
Score(p) = 1 / (1 + log10( T(p) / T*(p) ))
```

Where:
- **T(p)** = wall-clock runtime of the configuration being evaluated on instance p
- **T\*(p)** = the **best known runtime** for instance p (the reference time)

### Scoring Rules

| Condition | Score |
|-----------|-------|
| Configuration **solved** the instance | `1 / (1 + log10(T(p)/T*(p)))` in (0, 1] |
| T(p) = T\*(p) (configuration IS the best) | **1.0** (maximum) |
| T(p) = 10 x T\*(p) (10x slower than best) | **0.5** |
| Configuration **did NOT solve** (TIMEOUT/FAILURE) | **0.0** |
| **No configuration** solved this instance (T\* undefined) | **0.0** for all |

### Aggregation

The **total IPC score** for a configuration across n instances is the **sum** of individual scores:

```
Total_IPC_Score = SUM of Score(p) for all p in (instance-01, ..., instance-19)
```

Maximum possible score per domain = **15.0** (one point per instance, 15 instances per domain).  
Maximum possible score across all domains = **75.0** (15 x 5 domains).

### Is This the Same as IPC Competitions?

**Yes, with one clarification.** The formula `1/(1+log10(T/T*))` is the standard IPC Agile Track scoring function. In official IPC competitions:
- T\* is determined by the best competitor across all submitted planners
- The timeout is typically 1800s (30 min) or 300s (5 min for Agile Track)

In our thesis:
- Our timeout is **360 seconds** (6 minutes), as defined in our experimental setup
- T\* is computed from our own experimental data (see Section 2)
- The formula itself is **identical** to the official IPC definition

---

## 2. Two T* Contexts: Configuration Sensitivity vs. Simulated Competition

We compute IPC scores under **two different definitions of T\***, each answering a different question:

### 2.1 Configuration Sensitivity (Per-Planner)

> **Question:** "How well does this configuration perform compared to the best this SAME planner has ever achieved?"

```
T*_config(planner, domain, instance) = min( T(p) across ALL stages, ALL LLMs, ALL configs )
                                        WHERE Planner_Used = planner
```

- T\* is specific to **each planner**
- A planner is only compared against **itself** across different domain configurations
- This isolates the effect of domain configuration on a specific planner
- **117 out of 300 (planner x domain x instance) combinations have T\* = UNSOLVED**

#### Solved Instance Counts (Configuration Sensitivity)

| Planner | barman | depots | ricochet-robots | snake | visitall | Total |
|---------|-------|-------|-------|-------|-------|-------|
| bfws | 15/15 | 15/15 | 13/15 | 8/15 | 15/15 | 66/75 |
| lama | 15/15 | 15/15 | 7/15 | 2/15 | 15/15 | 54/75 |
| decstar | 4/15 | 14/15 | 5/15 | 3/15 | 0/15 | 26/75 |
| madagascar | 13/15 | 15/15 | 0/15 | 9/15 | 0/15 | 37/75 |
| **TOTAL** | 47/60 | 59/60 | 25/60 | 22/60 | 30/60 | **183/300** |

### 2.2 Simulated Competition (All Planners)

> **Question:** "How well does this configuration perform compared to the absolute best ANY planner has ever achieved?"

```
T*_comp(domain, instance) = min( T(p) across ALL planners, ALL stages, ALL LLMs, ALL configs )
```

- T\* is **shared across all planners** — every planner competes against the global best
- A slow planner on an easy instance (where another planner is very fast) will score low even if it solved it
- This simulates a real planning competition scenario
- **6 out of 75 (domain x instance) combinations have T\* = UNSOLVED**

#### Solved Instance Counts (Simulated Competition)

| Domain | Solved/15 |
|--------|-----------|
| barman | 15/15 |
| depots | 15/15 |
| ricochet-robots | 14/15 |
| snake | 10/15 |
| visitall | 15/15 |
| **TOTAL** | **69/75** |

### 2.3 Key Differences Summary

| Aspect | Configuration Sensitivity | Simulated Competition |
|--------|--------------------------|----------------------|
| T\* scope | Per-planner (same planner only) | Global (all planners) |
| T\* granularity | (planner, domain, instance) | (domain, instance) |
| Total T\* entries | 300 | 75 |
| Unsolved T\* entries | 117 | 6 |
| What it measures | Effect of domain config on a specific planner | Absolute competitive position |
| Fair comparison? | Yes — planners compared to themselves | Cross-planner comparison (favors fast planners) |
| Use case | "Did arch-aware prompting help LAMA?" | "Which stage produces the overall best configs?" |

### 2.4 How T\* Was Computed

For **both** contexts, T\* was computed by scanning **ALL 7,350 rows** in `planner_execution_data.csv`, which includes:

| Stage | Description | Rows |
|-------|-------------|------|
| BASELINE (S0) | Original domains, 4 planners x 5 domains x 15 instances | 300 |
| General (S1) | General prompt, 4 LLMs x 4 planners x 5 domains x 15 instances | 1,080 |
| Arch_Aware (S2-target) | Arch-aware prompt, target planner only | 1,125 |
| Cross_Test (S2-cross) | Arch-aware domains tested on non-target planners | 1,890 |
| Feedback_Loop1 (S3-iter1) | Feedback loop iteration 1 | 1,125 |
| Feedback_Loop2 (S3-iter2) | Feedback loop iteration 2 | 945 |
| Feedback_Loop3 (S3-iter3) | Feedback loop iteration 3 | 885 |
| **TOTAL** | | **7,350** |

> [!IMPORTANT]
> T\* includes data from ALL stages. This means if a Feedback Loop iteration produced the fastest time for an instance, that becomes T\*. This is the correct approach because T\* should represent the absolute best achievable time, giving a fair scoring baseline.

---

## 3. Detailed T\* Reference Values

The complete T\* reference tables are saved as CSV files:
- `T_star_reference.csv` in each context's output folder
- Each entry shows the T\* value, which stage produced it, and which LLM (if applicable)

The CSV files contain every (planner, domain, instance) triple for Configuration Sensitivity and every (domain, instance) pair for Simulated Competition.

---

## 4. Output Files Generated

### Configuration Sensitivity

| File | Description |
|------|-------------|
| `S0_Baseline_IPC.csv` | Stage 0: 4 planners x 5 domains IPC scores |
| `S1_General_<LLM>.csv` (x4) | Stage 1: 4 planners x 5 domains, one table per LLM |
| `S2_ArchAware_<LLM>.csv` (x4) | Stage 2: 4 planners x 20 (domain, prompt-target) columns, one per LLM |
| `S3_FeedbackLoop_All_Iterations.csv` | Stage 3: All 218 iterations with IPC scores |
| `T_star_reference.csv` | All T\* values with source stage annotations |

### Simulated Competition

Same file structure, in the `Simulated_Competition/` subfolder.
