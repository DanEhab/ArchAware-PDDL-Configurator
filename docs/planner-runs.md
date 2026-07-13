# 📊 How the 7,350 Planner Runs Are Divided

Every experiment stage was run separately, and every single planner execution — success or timeout — is recorded in a `*_planner_execution_data.csv` file under [`results/`](../results/). The totals below add up to **7,350** runs.

| Stage | Runs | How it breaks down | Data file |
|---|:--:|---|---|
| **0 · Baseline** | **300** | 4 planners × 5 domains × 15 instances | [`results/base/`](../results/base/) |
| **1 · General Prompt** | **1,080** | 18 validated domains × 4 planners × 15 instances | [`results/general_prompt/`](../results/general_prompt/) |
| **2 · Architecture‑Aware** (on target) | **1,125** | 75 validated configurations × 15 instances (each run on its *target* planner) | [`results/arch_aware/`](../results/arch_aware/) |
| **2 · Cross‑Testing** | **1,890** | 42 improved configurations × 3 *non‑target* planners × 15 instances | [`results/cross_test/`](../results/cross_test/) |
| **3 · Feedback Loop** | **2,955** | 80 triples enter the loop (≤ 3 telemetry‑driven iterations each); the validated iterations produced 2,955 runs | [`results/feedback_loop/`](../results/feedback_loop/) |
| **Total** | **7,350** | | |

### Notes
- A **"run"** is one planner solving one problem instance in one Docker container (1 CPU · 8 GB · 360 s timeout).
- Counts differ from the theoretical maxima because some LLM outputs fail validation (and so are never executed), and some feedback‑loop triples terminate early — for example, the 12 planner–domain pairs that time out on every instance stop after a single iteration.
- The full experimental grid is **4 planners × 4 LLMs × 5 domains × 15 instances**, defined in [`config/experiment_config.yaml`](../config/experiment_config.yaml).

---
← Back to the [README](../README.md)
