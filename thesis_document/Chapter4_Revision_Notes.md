# Chapter 4 — Revision Notes (content & structure pass)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Scope:** Revisions to `04-design.tex` (plus coordinated touches to `05-implementation.tex` and `06-experimental-setup.tex`), acting on your six instructions.
**Date:** 26 June 2026

> Everything below is **already applied**. There is **one action for you** (the real `experiment_config.yaml`) — see the box in §2. Recompile to see the result.

---

## 1. Implementation detail moved out of Chapter 4 (your point 1)

I read Chapter 5 in full first. Key realisation: **Chapter 5 already contained almost all of the implementation mechanics**, so Chapter 4 and Chapter 5 were *repeating* each other. The right fix was therefore to **trim Chapter 4 to the design level and point to Chapter 5**, not to copy text across. Chapter 4 now answers *what* and *why*; Chapter 5 owns *how*.

**Removed from Chapter 4 (it already lives in Chapter 5):**

| Detail removed from Ch. 4 | Now lives in Ch. 5 |
|---|---|
| `ThreadPoolExecutor`, "thread-safe CSV manager protected by a mutual exclusion lock" (§4.2) | `csv_manager.py` (Table 5.1) |
| `threading.Lock`, auto-incrementing IDs, the whole "Thread-safe data persistence" safeguard paragraph (§4.7) | `csv_manager.py` (Table 5.1) |
| Hash-set / `O(1)` checkpoint mechanism (§4.1, §4.3, §4.7) | `csv_manager.py` checkpointing (Table 5.1) |
| "Logging infrastructure" paragraph — `pipeline_heartbeat.log` (60 s daemon), `TeeLogger`, `error_register.csv` (§4.1.1) | `heartbeat.py`, `error_handler.py` (Table 5.1) + a new sentence I added to §5.1.2 so the terminal-output capture isn't lost |
| Explicit CSV file names (`planner_execution_data.csv`, `llm_generation_data.csv`) and the "dual-write" wording (§4.1.1) | §5.1, Fig. 5.1, Table 5.1 |
| `--memory-swap` Docker flag detail (§4.7) | `docker run` listing (§5.2.2) |

**Kept in Chapter 4 (correctly design-level):** the staged ablation, the four-stage run counts, the data **architecture** (the two measurement schemas, Tables 4.1–4.2 — they define *what is measured*), the validation-pipeline *logic* (V1–V4), the improvement test, and the safeguard *rationale* (why containers, single core, 8 GB, 360 s, T = 0.0, dedicated hardware). Each trimmed spot now carries a forward reference (`\Cref{ch:implementation}`, `\Cref{sec:impl:docker}`, `\Cref{sec:impl:llm_integration}`).

Net effect: no more Ch. 4 ↔ Ch. 5 duplication, and §4.1.1 and §4.7 read as crisp design prose.

---

## 2. α = 0.25 reframed as a screening gate (your point 2)

I verified the **actual code** (`experiments/arch-aware/improvement/run_improvement_test.py`): it uses `P_VALUE_THRESHOLD = 0.25` and `MEAN_GAIN_THRESHOLD = 0.0`. So your account is exactly right, and Chapter 4's three conditions already match the code (Condition B "mean gain > 0" = `MEAN_GAIN_THRESHOLD = 0.0`).

I rewrote **Condition A** so the 0.25 is presented the way you described it — as a deliberate **internal selection gate** (deciding which configurations advance to cross-planner testing), *not* a significance claim — and I state explicitly that the **confirmatory analyses in Chapter 7 use α = 0.05**. The new text explains that a 0.05 gate here would discard candidates worth cross-architecture investigation, that the relaxed gate favours *recall*, and that Conditions B and C guard against false positives. This is now defensible and clearly worded for an examiner.

> ### ⚠️ Action for you (repository consistency)
> Your real config file `config/experiment_config.yaml` still says `alpha: 0.05` and `min_mean_gain: 0.05` under `improvement_detection`, but the code overrides these with **0.25** and **0.0**. I updated the **thesis** (Ch. 6 config excerpt) to show **0.25 / 0.0** so it matches what actually ran and what Ch. 4 says. **Please update the actual YAML file to `alpha: 0.25` and `min_mean_gain: 0.0`** (and, ideally, make `run_improvement_test.py` read these from the config instead of hard-coding them) so the repository, the code, and the thesis all agree. Otherwise an examiner who opens the repo will see 0.05 where the thesis says 0.25.

---

## 3. The two IPC reference-time (T\*) definitions — now justified (your point 3)

Rather than treat the two definitions as an inconsistency, I added the rationale you gave so they read as deliberate, principled choices:

- **Stage 2 (§4.4.3):** added a sentence noting that T\* is the best time *observed so far*, so the score is a within-pipeline **screening** signal, and that **Chapter 7 recomputes all IPC scores against a single, globally consistent reference** once the whole experiment is finished (matching how your Phase-5 analysis in `analysis/` works).
- **Stage 3 (§4.5, iteration loop):** added a short explanation that T\* is restricted to the baseline + current iteration to avoid a **"moving reference"** — since each iteration adds new timing data, including later iterations would make an earlier iteration's score depend on results that did not yet exist, which would be unfair. Restricting it gives a stable per-iteration verdict.

A reader now sees three coherent, purpose-matched uses of the same formula (per-stage screening, per-iteration verdict, and final global comparison).

---

## 4. PAR10 removed from Chapter 4 (your point 4)

You confirmed PAR10 was never computed in any stage — only in the Chapter 7 cross-analysis. I removed both Chapter 4 mentions (the "PAR10 ratios" in §4.2 and "for PAR10 … computation" in §4.7), so Chapter 4 no longer implies PAR10 is part of the pipeline. It will be introduced properly where it is actually used (Chapter 7 / the evaluation-metrics discussion).

---

## 5. Table of Contents (your point 5)

The chapter previously toggled `tocdepth` four times, which made the TOC show subsections **only** for §4.6 — and one toggle (at the chapter end) even turned subsections on for *all later chapters*, conflicting with the thesis default. The global default in `config.tex` is already `tocdepth = 1` (sections only). I **removed all four toggles**, so Chapter 4 now shows **no subsections** in the TOC — consistent with every other chapter, and exactly the "not scary" TOC you wanted.

---

## 6. Other polish (your point 6)

- Fixed the four paragraph/chapter openings that began with "This" (IAAS guideline) — including the chapter's first sentence.
- Tightened §4.1's principle bullets ("reproducibility", "data capture") to design-level statements with forward references.
- Verified all figures (4.1 pipeline, 4.2 validation), tables (4.1–4.4), listings (4.1–4.3), and equations (4.1–4.7) — captions, cross-references, and arithmetic all check out and were already correct; the prose around them is now leaner.
- Confirmed every cross-reference label used in the new text resolves, and that no citation keys were affected.

---

## Coordination summary (Ch. 4 ↔ Ch. 5)

- **Chapter 4** = abstract design: stages, data architecture (measurement schemas), validation logic, improvement test, safeguard rationale.
- **Chapter 5** = realisation: code structure, `csv_manager`/`heartbeat`/`error_handler` modules, Docker invocation and images, planner builds, VAL integration, LLM provider layer.
- Added one sentence to §5.1.2 so the terminal-output logging (formerly only in Ch. 4) is preserved in Ch. 5.
- No remaining duplicated mechanics between the two chapters; trimmed spots in Ch. 4 cross-reference Ch. 5.

## Files changed
- `content/04-design.tex` — all of the above (≈ 20 edits).
- `content/05-implementation.tex` — one sentence added (§5.1.2) to preserve terminal-output logging.
- `content/06-experimental-setup.tex` — config excerpt `alpha: 0.05 → 0.25`, `min_mean_gain: 0.05 → 0.0` (to match the code and Ch. 4).

*Please recompile. The only manual follow-up is the `experiment_config.yaml` update in the ⚠️ box above.*
