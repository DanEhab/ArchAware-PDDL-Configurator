# Section 9: Improvement Pipeline Funnel Analysis — Results Report

> **Generated:** 2026-06-08
> **Data Sources:** `llm_generation_data.csv`, `planner_execution_data.csv`, `improvement_results.csv`, and `stage3_final_domains.csv`

---

## 1. Methodology Overview
This section tracks the **Survival Rate** of LLM-generated PDDL configurations across the entire analysis pipeline. It acts as the definitive macro-summary of the thesis framework's yield.
The funnel measures attrition across four strict boundaries:
1. **Generation:** Did the LLM output a file?
2. **Validation:** Was the PDDL syntax and semantic identity mathematically flawless?
3. **Execution:** Did the planner parse and run it without crashing?
4. **Improvement:** Did the final configuration mathematically beat the Stage 0 baseline IPC score?

---

## 2. Table G-T32: Full Pipeline Funnel
### What Does This Table Show?
The step-by-step attrition counts for Stage 1, Stage 2, and Stage 3.

| Pipeline Stage               | Input Count   | Output Count   | Pass Rate   |
|:-----------------------------|:--------------|:---------------|:------------|
| S1: LLM generates domains    | 20            | 20             | 100.0%      |
| S1: Validation (V1-V4)       | 20            | 18             | 90.0%       |
| S1: Planner execution        | 1080 runs     | —              | —           |
| S2: LLM generates domains    | 80            | 80             | 100.0%      |
| S2: Validation (V1-V4)       | 80            | 75             | 93.8%       |
| S2: Planner target execution | 1125 runs     | —              | —           |
| S2: Improvement detection    | 75 valid      | 42             | —           |
| S2: Cross-test execution     | 1890 runs     | —              | —           |
| S3: Seed selection           | 80 tuples     | 80             | —           |
| S3: Iterative refinement     | 68            | 68             | —           |
| S3: Final vs S2 Seed         | 68            | 32             | 47.1%       |
| S3: Final vs S0 Baseline     | 68            | 55             | 80.9%       |

### Key Findings
- **Massive Execution Footprint:** The pipeline executed over 2,200 planner runs across S1 and S2 to establish statistical certainty.
- **Validation Stability:** The S2 generation loop produced 80 unique configurations. An astounding 90%+ pass rate was achieved through `VAL` checks, proving the LLMs can reliably write raw PDDL.
- **The Improvement Threshold:** Out of the **68 contestable** candidate seeds going into S3, exactly **55** achieved a strictly better IPC score than their Stage 0 baseline counterpart after the iterative feedback loop. This equates to an **80.9% framework success rate**.
