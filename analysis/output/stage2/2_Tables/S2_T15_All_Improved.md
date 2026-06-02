# S2-T15: Complete Improved Configurations

| Domain          | LLM         | Target Planner   |   Mean IPC Gain |   p-value |   Base Cov |   S2 Cov |   Delta Cov |
|:----------------|:------------|:-----------------|----------------:|----------:|-----------:|---------:|------------:|
| depots          | Claude 4.6  | bfws             |           0.085 |     0.003 |   1        | 1        |    0        |
| depots          | DeepSeek-R1 | madagascar       |           0.078 |     0.001 |   1        | 1        |    0        |
| snake           | Claude 4.6  | madagascar       |           0.077 |     0.234 |   0.4      | 0.466667 |    0.066667 |
| depots          | DeepSeek-R1 | bfws             |           0.074 |     0     |   1        | 1        |    0        |
| depots          | Gemini 3.1  | madagascar       |           0.068 |     0     |   1        | 1        |    0        |
| depots          | DeepSeek-R1 | lama             |           0.054 |     0     |   1        | 1        |    0        |
| depots          | GPT-5.4     | madagascar       |           0.054 |     0     |   1        | 1        |    0        |
| depots          | Gemini 3.1  | bfws             |           0.05  |     0     |   1        | 1        |    0        |
| depots          | Claude 4.6  | madagascar       |           0.045 |     0.001 |   1        | 1        |    0        |
| barman          | Gemini 3.1  | bfws             |           0.04  |     0     |   1        | 1        |    0        |
| depots          | GPT-5.4     | lama             |           0.035 |     0     |   1        | 1        |    0        |
| depots          | Claude 4.6  | lama             |           0.034 |     0     |   1        | 1        |    0        |
| depots          | Claude 4.6  | decstar          |           0.032 |     0     |   0.933333 | 0.933333 |    0        |
| barman          | DeepSeek-R1 | lama             |           0.026 |     0     |   1        | 1        |    0        |
| depots          | DeepSeek-R1 | decstar          |           0.026 |     0     |   0.933333 | 0.933333 |    0        |
| visitall        | GPT-5.4     | lama             |           0.026 |     0     |   1        | 1        |    0        |
| barman          | GPT-5.4     | bfws             |           0.025 |     0     |   1        | 1        |    0        |
| visitall        | Gemini 3.1  | lama             |           0.023 |     0.011 |   1        | 1        |    0        |
| depots          | GPT-5.4     | decstar          |           0.023 |     0     |   0.933333 | 0.933333 |    0        |
| snake           | Gemini 3.1  | madagascar       |           0.022 |     0.148 |   0.4      | 0.4      |    0        |
| ricochet-robots | Gemini 3.1  | bfws             |           0.02  |     0.027 |   0.733333 | 0.733333 |    0        |
| visitall        | DeepSeek-R1 | lama             |           0.019 |     0.018 |   1        | 1        |    0        |
| visitall        | Claude 4.6  | lama             |           0.019 |     0.053 |   1        | 1        |    0        |
| depots          | Gemini 3.1  | lama             |           0.018 |     0.004 |   1        | 1        |    0        |
| visitall        | Claude 4.6  | bfws             |           0.018 |     0.001 |   1        | 1        |    0        |
| barman          | GPT-5.4     | lama             |           0.015 |     0     |   1        | 1        |    0        |
| visitall        | GPT-5.4     | bfws             |           0.013 |     0.227 |   1        | 1        |    0        |
| snake           | Gemini 3.1  | decstar          |           0.013 |     0.125 |   0.2      | 0.2      |    0        |
| snake           | GPT-5.4     | bfws             |           0.013 |     0.055 |   0.533333 | 0.533333 |    0        |
| snake           | DeepSeek-R1 | decstar          |           0.013 |     0.125 |   0.2      | 0.2      |    0        |
| barman          | DeepSeek-R1 | bfws             |           0.013 |     0     |   1        | 1        |    0        |
| barman          | Claude 4.6  | bfws             |           0.012 |     0.053 |   1        | 1        |    0        |
| barman          | Claude 4.6  | lama             |           0.01  |     0.001 |   1        | 1        |    0        |
| snake           | GPT-5.4     | lama             |           0.007 |     0.25  |   0.133333 | 0.133333 |    0        |
| snake           | Gemini 3.1  | lama             |           0.006 |     0.25  |   0.133333 | 0.133333 |    0        |
| snake           | Claude 4.6  | lama             |           0.006 |     0.25  |   0.133333 | 0.133333 |    0        |
| snake           | DeepSeek-R1 | lama             |           0.006 |     0.25  |   0.133333 | 0.133333 |    0        |
| ricochet-robots | DeepSeek-R1 | lama             |           0.004 |     0.016 |   0.4      | 0.4      |    0        |
| snake           | Claude 4.6  | decstar          |           0.002 |     0.125 |   0.2      | 0.2      |    0        |
| ricochet-robots | Gemini 3.1  | lama             |           0.002 |     0.047 |   0.4      | 0.4      |    0        |
| ricochet-robots | Claude 4.6  | lama             |           0.001 |     0.109 |   0.4      | 0.4      |    0        |
| barman          | Claude 4.6  | decstar          |           0     |     0.188 |   0.266667 | 0.266667 |    0        |
