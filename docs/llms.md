# 🤖 The Four LLMs

Four frontier large language models are used as the domain configurators, split into two architectural families to balance the evaluation. All are accessed via their provider APIs with **version‑pinned endpoints** and deterministic decoding (`temperature = 0.0`, stateless calls) for reproducibility.

| Model | Provider | Category | Exact version / endpoint |
|---|---|---|---|
| **GPT‑5.4** | OpenAI | Deep‑reasoning | `gpt-5.4-2026-03-05` |
| **DeepSeek‑R1** | DeepSeek | Deep‑reasoning | `deepseek-reasoner` |
| **Claude Opus 4.6** | Anthropic | Coding heavyweight | `claude-opus-4-6` |
| **Gemini 3.1 Pro** | Google | Coding heavyweight | `gemini-3.1-pro-preview-customtools` |

*Deep‑reasoning* models allocate significant inference‑time computation to evaluate multiple reasoning paths; *coding‑heavyweight* models are optimised for syntax comprehension and code generation. All model IDs and hyperparameters are defined centrally in [`config/experiment_config.yaml`](../config/experiment_config.yaml).

---
← Back to the [README](../README.md)
