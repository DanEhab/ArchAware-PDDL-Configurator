# S2-T22: Specialization Verdict per Configuration

| Domain          | LLM         | Target Planner   |   Target Gain |   Avg Non-Target Gain |   Specialization Index | Verdict            |
|:----------------|:------------|:-----------------|--------------:|----------------------:|-----------------------:|:-------------------|
| Visitall        | GPT-5.4     | BFWS             |        0.0556 |               -0.0558 |                 0.1115 | Specialized        |
| Visitall        | Claude 4.6  | BFWS             |        0.0395 |               -0.0602 |                 0.0996 | Specialized        |
| Depots          | DeepSeek-R1 | BFWS             |        0.1372 |                0.0424 |                 0.0947 | Universally Better |
| Visitall        | GPT-5.4     | LAMA             |        0.0259 |               -0.0637 |                 0.0896 | Specialized        |
| Visitall        | DeepSeek-R1 | LAMA             |        0.0155 |               -0.0725 |                 0.0879 | Specialized        |
| Snake           | Gemini 3.1  | MADAGASCAR       |        0.0795 |               -0.0084 |                 0.0879 | Specialized        |
| Visitall        | Gemini 3.1  | LAMA             |        0.0202 |               -0.0623 |                 0.0826 | Specialized        |
| Depots          | Claude 4.6  | BFWS             |        0.1287 |                0.0499 |                 0.0788 | Universally Better |
| Snake           | DeepSeek-R1 | DECSTAR          |        0.0289 |               -0.0398 |                 0.0687 | Specialized        |
| Barman          | DeepSeek-R1 | LAMA             |        0.0418 |               -0.0266 |                 0.0685 | Specialized        |
| Snake           | Claude 4.6  | LAMA             |        0.0133 |               -0.054  |                 0.0673 | Specialized        |
| Visitall        | Claude 4.6  | LAMA             |        0.0099 |               -0.0549 |                 0.0648 | Specialized        |
| Barman          | Gemini 3.1  | BFWS             |        0.0755 |                0.0188 |                 0.0567 | Universally Better |
| Depots          | Gemini 3.1  | BFWS             |        0.1008 |                0.0467 |                 0.0542 | Universally Better |
| Depots          | DeepSeek-R1 | MADAGASCAR       |        0.1165 |                0.0684 |                 0.0481 | Universally Better |
| Snake           | Gemini 3.1  | LAMA             |        0.0134 |               -0.0316 |                 0.045  | Specialized        |
| Depots          | DeepSeek-R1 | LAMA             |        0.0989 |                0.056  |                 0.0428 | Universally Better |
| Ricochet-robots | Gemini 3.1  | BFWS             |        0.0436 |                0.0034 |                 0.0402 | Neutral            |
| Depots          | Gemini 3.1  | MADAGASCAR       |        0.1091 |                0.0751 |                 0.034  | Universally Better |
| Barman          | DeepSeek-R1 | BFWS             |        0.0179 |               -0.0155 |                 0.0333 | Specialized        |
| Snake           | DeepSeek-R1 | LAMA             |        0.0131 |               -0.0124 |                 0.0255 | Specialized        |
| Ricochet-robots | Claude 4.6  | LAMA             |        0.0021 |               -0.0226 |                 0.0247 | Specialized        |
| Snake           | Gemini 3.1  | DECSTAR          |        0.0303 |                0.006  |                 0.0242 | Universally Better |
| Snake           | Claude 4.6  | DECSTAR          |        0.0063 |               -0.0158 |                 0.0221 | Specialized        |
| Depots          | GPT-5.4     | MADAGASCAR       |        0.0869 |                0.0681 |                 0.0188 | Universally Better |
| Depots          | Claude 4.6  | LAMA             |        0.0667 |                0.0501 |                 0.0166 | Universally Better |
| Barman          | Claude 4.6  | BFWS             |        0.0144 |               -0.0001 |                 0.0145 | Neutral            |
| Ricochet-robots | Gemini 3.1  | LAMA             |        0.0039 |               -0.0104 |                 0.0143 | Specialized        |
| Depots          | Claude 4.6  | MADAGASCAR       |        0.069  |                0.0556 |                 0.0135 | Universally Better |
| Ricochet-robots | DeepSeek-R1 | LAMA             |        0.0087 |               -0.0044 |                 0.0131 | Neutral            |
| Depots          | GPT-5.4     | LAMA             |        0.0696 |                0.0615 |                 0.0081 | Universally Better |
| Snake           | GPT-5.4     | LAMA             |        0.015  |                0.0086 |                 0.0064 | Universally Better |
| Barman          | GPT-5.4     | BFWS             |        0.0423 |                0.0382 |                 0.0041 | Universally Better |
| Snake           | GPT-5.4     | BFWS             |        0.0311 |                0.0286 |                 0.0025 | Universally Better |
| Barman          | GPT-5.4     | LAMA             |        0.0246 |                0.0357 |                -0.0111 | Anti-Specialized   |
| Depots          | Gemini 3.1  | LAMA             |        0.0425 |                0.0553 |                -0.0128 | Anti-Specialized   |
| Barman          | Claude 4.6  | LAMA             |        0.0151 |                0.0401 |                -0.0249 | Anti-Specialized   |
| Snake           | Claude 4.6  | MADAGASCAR       |        0.0054 |                0.0371 |                -0.0318 | Anti-Specialized   |
| Depots          | Claude 4.6  | DECSTAR          |        0.0593 |                0.092  |                -0.0327 | Anti-Specialized   |
| Barman          | Claude 4.6  | DECSTAR          |        0.0001 |                0.035  |                -0.0349 | Anti-Specialized   |
| Depots          | DeepSeek-R1 | DECSTAR          |        0.0427 |                0.0941 |                -0.0513 | Anti-Specialized   |
| Depots          | GPT-5.4     | DECSTAR          |        0.0339 |                0.0855 |                -0.0516 | Anti-Specialized   |
