# Coherence Review — Chapters 4, 5 & 6 as a Unit

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Scope:** Chapters 4 (Design), 5 (Implementation), 6 (Experimental Setup) read together — division of labour, flow, factual conflicts, repetition, and cross-reference integrity.
**Date:** 26 June 2026

> **Verdict:** These three chapters now form a **clean, conflict-free progression** with a coherent division of labour. I found **no factual contradictions**, and I removed the **five repetitions** that did exist (two substantial, three minor) — each by keeping the content in its correct chapter and cross-referencing from the others. Everything below documents the checks and the changes.

---

## Part A — Division of labour (now clean)

The three chapters answer three different questions, with almost no overlap after this pass:

| Chapter | Question it answers | Owns (uniquely) |
|---|---|---|
| **4 — Design** | *What* does the pipeline do, and *why*? | The four-stage ablation, validation-pipeline **logic** (V1–V4), improvement-detection test (IPC score, three conditions, α-screening), data **architecture** (measurement schemas), safeguard **rationale**. |
| **5 — Implementation** | *How* is it built? | Codebase/modules, Docker **mechanics** (the `docker run` command, images), planner **integration** (provenance, builds, invocation, metric parsing), VAL container, LLM **provider/SDK** layer + error handling. |
| **6 — Experimental Setup** | *Which* concrete ingredients, and on what justification? | Planner/domain/LLM/prompt **selection + rationale**, structural-diversity quantification, hardware **table**, hyperparameter **values**, instance selection, the config file. |

The boundary that was fuzziest before — design vs. implementation — is now sharp after the Chapter 4 trim: mechanics (threading, checkpointing, logging daemons, Docker flags) live only in Chapter 5, and Chapter 4 references them.

---

## Part B — Flow and continuity

The chapters chain explicitly, which is exactly what you want:

- **Ch. 4 → Ch. 5:** Chapter 5 opens by naming the hand-off — *"Chapter 4 specified what the pipeline does … the present chapter explains how each component was built."* This is a model transition.
- **Ch. 4/5 → Ch. 6:** Chapter 6 opens by referencing the design it parameterises (*"the pipeline designed in Chapter 4"*), and the safeguard rationale in §4.7 forward-references the hardware/hyperparameters in Chapter 6.
- **One structural subtlety, well-handled:** the planners/domains/LLMs are *integrated* in Chapter 5 but *selected/justified* in Chapter 6 (which comes after). Strictly, "why we chose them" follows "how we wired them in." This is a consequence of the Design → Implementation → Setup ordering, and Chapter 5 handles it correctly with an explicit forward reference (*"the rigorous methodology for selecting these four planners is detailed in §6.1; this section describes how they were integrated"*). It reads fine; no change needed. (If you ever wanted the more conventional order, you would swap Chapters 5 and 6 — but I do **not** recommend it; the current order matches the IAAS Design→Realisation→Evaluation structure and the forward references make it flow.)

---

## Part C — Conflict / contradiction check (none found)

I cross-checked every shared fact across the three chapters; all agree:

| Quantity | Ch. 4 | Ch. 5 | Ch. 6 | Status |
|---|---|---|---|---|
| Domains / planners / LLMs | 5 / 4 / 4 | 5 (dir tree) / 4 / 4 | 5 / 4 / 4 | ✅ |
| Instances per domain | 15 | — | 15 (seed 42) | ✅ |
| Time limit | 360 s (+375 s host) | 360 s | 360 s | ✅ |
| Memory | 8 GB, no swap | `--memory=8g --memory-swap=8g` | 8 GB, swap disabled | ✅ |
| CPU | 1 core | `--cpus=1.0` | 1 core | ✅ |
| Temperature / tokens / state | T=0.0, stateless | T=0.0 (SDK note) | T=0.0, 8192, stateless | ✅ |
| α / min-gain (screening) | 0.25 / >0 | — | 0.25 / 0.0 | ✅ |
| DecStar IPC 2023 | — | "won … Agile Track" | "Winner … Agile track" | ✅ (now consistent) |
| Planner names / domain names | generic | full names | full names | ✅ |

No metric, parameter, name, or claim contradicts across the three chapters.

---

## Part D — Repetitions found and removed

Two were substantial (near-verbatim), three were minor. All are now fixed by keeping the text in one chapter and referencing it from the other(s):

1. **Hardware rationale (substantial).** The "shared cloud / noisy-neighbour / hypervisor steal / dedicated hardware / Wilcoxon-noise" justification appeared almost word-for-word in both §4.7 *and* §6.6 — and §6.6 even said "as motivated in §4.7" before repeating it. **Kept** the full rationale in §4.7 (safeguards); **trimmed** §6.6 to a one-line reference before the hardware table.
2. **LLM hyperparameters (substantial).** §5.5.3 and §6.7.1 both defined T=0.0, the deep-reasoning omission, max-tokens, and statelessness. **Kept** the values + empirical justification in §6.7.1 (setup); **trimmed** §5.5.3 to the one genuinely implementation-specific point (the SDK omitting temperature/top-p for reasoning models) with a reference to §6.7.
3. **`N/A`-vs-`0` rationale (minor).** Explained in both §4.1.1 and §5.2.1. **Kept** the rationale in §4.1.1 (data architecture); **trimmed** §5.2.1 to the implementation fact + a reference.
4. **Docker resource flags (minor).** The exact `--cpus`/`--memory-swap`/`oom-kill-disable` flags appeared in both the §5.2.2 command and the §6.7.2 bullet list. **Kept** the flags in §5.2.2 (the command); **trimmed** §6.7.2 to the constraint *values* with a reference to §5.2.
5. **"Centralised config for reproducibility" (minor, internal to Ch. 6).** Stated in both the chapter intro and the §6.7 opener. **Trimmed** the §6.7 opener to avoid the echo.

**Repetition that is appropriate and was kept:** the *same metric value* legitimately appearing in a config listing and in prose (e.g., 360 s in both Listing 6.1 and §6.7.2 text); brief restatements of "T=0.0" as a one-clause safeguard in §4.7 vs. the full treatment in §6.7. These are cross-referential, not redundant.

---

## Part E — Cross-reference integrity

All inter-chapter references resolve (verified each `\label` target exists): §4.7 ↔ §6.6/§6.7; §5 ↔ §4.6/§4.7/§6.1/§6.7; §6 ↔ §4 design and §5 implementation. The new references added during de-duplication (`sec:setup:hyperparameters`, `sec:impl:docker`, `sec:design:overview:data`) all point to existing labels. No dangling or circular references.

---

## Part F — Changelog (this pass)

**`content/05-implementation.tex`**
- §5.5.3 (Hyperparameter Control): trimmed to the SDK-specific point; values/justification now deferred to §6.7 (`\Cref{sec:setup:hyperparameters}`).
- §5.2.1: trimmed the duplicated `N/A`-vs-`0` rationale; now references §4.1.1.

**`content/06-experimental-setup.tex`**
- §6.6: removed the verbatim hardware/Wilcoxon rationale; now one line referencing §4.7 before the table.
- §6.7.2: removed the duplicated Docker flag names from the bullets; now references the §5.2 command.
- §6.7 opener: removed the "centralised config" echo of the chapter intro.

*(No changes to Chapter 4 this pass — its content is already in the right place after the previous revision.)*

---

## Part G — One thing to keep in mind (not a Ch. 4–6 problem)

The only forward dependency left open is the one we already discussed: the **evaluation metrics** (coverage, the final global IPC score, PAR10, runtime, plan cost, validity rates, token efficiency) are not defined in Chapters 4–6, by your choice to define them per-stage in Chapter 7. That is fine for the 4–6 unit, but it means **Chapter 7 must define each metric on first use** — especially PAR10, which currently appears nowhere. I'll check this specifically when we review Chapter 7.

---

### Bottom line
Chapters 4–6 now read as one continuous, non-repetitive arc: **design the pipeline → build it → specify and justify the exact experiment.** No conflicts, clean hand-offs, and the duplications are gone. Recompile and skim the §6.6 and §6.7 areas to confirm the trimmed paragraphs read smoothly.
