# S3-T25: Output Token Efficiency by LLM

| LLM                                |   Total Output Tokens |   Mean Output Tokens | Improvement Rate   |   Mean Improvement vs Seed |   Tokens per IPC Point |
|:-----------------------------------|----------------------:|---------------------:|:-------------------|---------------------------:|-----------------------:|
| claude-opus-4-6                    |                54,159 |                1,003 | 47.1%              |                      0.097 |                 557000 |
| deepseek-reasoner                  |               180,741 |                3,228 | 35.3%              |                      0.212 |                 851826 |
| gemini-3.1-pro-preview-customtools |                43,005 |                  796 | 58.8%              |                      2.2   |                  19550 |
| gpt-5.4-2026-03-05                 |                42,035 |                  778 | 47.1%              |                      1.656 |                  25389 |
