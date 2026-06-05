# S3-T10: Specific Recovery Cases

| Domain          | LLM                                | Target_Planner   |   Best_Iteration |   Best_IPC_Score |   Improvement_vs_Seed | Better than Baseline?   |
|:----------------|:-----------------------------------|:-----------------|-----------------:|-----------------:|----------------------:|:------------------------|
| barman          | gemini-3.1-pro-preview-customtools | lama             |                3 |         14.9991  |              14.9991  | True                    |
| barman          | gemini-3.1-pro-preview-customtools | decstar          |                1 |          3.91703 |               3.91703 | False                   |
| depots          | gemini-3.1-pro-preview-customtools | decstar          |                1 |         13.7037  |              13.7037  | False                   |
| depots          | gpt-5.4-2026-03-05                 | bfws             |                3 |         14.5822  |              14.5822  | True                    |
| ricochet-robots | gpt-5.4-2026-03-05                 | lama             |                2 |          7       |               7       | True                    |
