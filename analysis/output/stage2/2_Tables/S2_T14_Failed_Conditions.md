# S2-T14: Failed Condition Analysis (Out of 33 Triples)

| Failed Condition Pattern                             |   Count | Description                                                        |
|:-----------------------------------------------------|--------:|:-------------------------------------------------------------------|
| Failed Statistical Significance (p > 0.25)           |      33 | Positive or negative gains, but not statistically significant.     |
| Failed Practical Significance (Mean IPC Gain <= 0)   |      27 | The modified domain performed worse, timed out, or had no gain.    |
| Zero Coverage (Baseline & Target)                    |      12 | Planner timed out on all instances for both baseline and modified. |
| Failed Coverage Preservation (Target Cov < Base Cov) |       7 | The modified domain solved fewer instances than the baseline.      |
