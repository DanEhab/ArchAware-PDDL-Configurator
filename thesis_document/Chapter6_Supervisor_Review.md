# Supervisor-Style Review — Chapter 6 (Experimental Setup)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 6 (`content/06-experimental-setup.tex`, 466 lines), cross-checked against Chapters 1–5, the repository, and the bibliography.
**Date:** 26 June 2026

> **Chapter 5 follow-ups (done this turn):** the CPLEX version is now **22.1.2** in all three places, and DecStar now reads **"won the Agile Track of the IPC 2023"** (which also removed a Ch5↔Ch6 inconsistency, since Ch6 already called DecStar the IPC 2023 Agile winner). I also re-scanned Ch5 — nothing else needs changing there.

> **Read order for Ch6.** Part A is the one important structural gap (a missing **Evaluation Metrics** section) — please read it first. Part B = the quality of the selection methodology (strong). Part C = references. Part D = figures/tables. Part E = specific smaller findings. Part F = guidelines + fixes applied. Part G = changelog. Part H = action items.

---

## Overall assessment

This is a **rigorous, genuinely impressive setup chapter.** The selections are not asserted but *argued*: planners via a four-filter funnel from 35 candidates, domains via a three-filter process backed by a quantified structural-diversity table, LLMs via an explicit two-category rationale, and prompts grounded in the predecessor's empirical results. I verified the externally checkable facts and they hold up: BFWS won the IPC 2018 Agile Track and DecStar-2023 won the IPC 2023 Agile Track; the domain-richness table genuinely spans the full range of every metric it claims; and the prior-work validity numbers (79.29% / 55.00% / 45.00% / 46.43% / 50.71%) match the predecessor study.

There is **one structural gap that matters**, and it is important: the chapter never defines the **evaluation metrics** the thesis will report. Everything else is small (three "This" openings, two cross-reference style fixes — all applied).

---

## Part A — The missing "Evaluation Metrics" section (top priority)

The chapter's own opening comment states its scope as *"the specific ingredients, rules, and **measurement instruments** of the experiment."* The ingredients (planners, domains, LLMs, prompts) and rules (hyperparameters, constraints) are covered thoroughly — but the **measurement instruments are never defined.** There is no section that defines:

- **Coverage** (how "solved" is counted),
- **IPC score** in its *final* form (Ch. 4 defines it only as a within-pipeline screening signal with a moving reference; Ch. 4 itself promises a "single, globally consistent reference" recomputed in Ch. 7 — that final definition has no home yet),
- **PAR10** (which I removed from Ch. 4 on the understanding it would be defined where it is actually used — it currently appears **nowhere** in the written thesis),
- **Runtime** (wall-clock vs internal), **plan cost**, **validity / semantic-equivalence rates**, and **token efficiency**.

Chapter 7 (Results) will report all of these, so they must be defined beforehand. The IAAS evaluation guideline explicitly lists "evaluation metrics" as a required component, and this setup chapter — already framed as the "measurement instruments" chapter — is the natural home.

**Recommendation:** add a section **§6.8 "Evaluation Metrics"** that defines each metric precisely (formula where appropriate), including the *final* global-reference IPC score that Ch. 7 uses, and PAR10 (penalised average runtime, with the timeout penalty factor stated). This single addition closes the loop with Chapters 4 and 7.

> **I can draft §6.8 for you.** To keep it exact, I would first pull the precise definitions you actually used (PAR10 penalty factor, the token-efficiency definition, the global IPC reference) from your `analysis/` scripts, then write the section to match. Just say the word and I'll add it.

---

## Part B — Selection methodology (strong; verified)

**Planners (§6.1).** The four-filter funnel (agile/no-portfolio → proven performance → reproducibility → *distinct architectures*) is well-reasoned, and Filter 4 (rejecting the Fast-Downward-monoculture of the IPC 2023 leaderboard) is exactly the right scientific instinct for a study about architectural diversity. Table 6.1 is accurate: BFWS = IPC 2018 Agile winner ✓, DecStar = IPC 2023 Agile winner ✓, LAMA/Madagascar as validated baselines ✓.

**Domains (§6.2).** The strongest part of the chapter. The structural-quantification table (Table 6.2) is verified internally consistent — the five domains span the full claimed ranges of every metric (|A| 1–12, |P| 3–15, |Pₘ| 1–9, |Oₜ| 0–7, arity 2–6), which substantiates the "maximal structural diversity" claim. The per-domain justifications (VisitAll = minimal baseline … Barman = maximal complexity anchor) are concrete and convincing, and the temporal spread (IPC 2002–2023) is a nice touch.

**LLMs (§6.3).** The two-category split (deep-reasoning vs coding-heavyweight) is a reasonable framework, and it is consistent with Ch. 5's hyperparameter handling (GPT-5.4 and DeepSeek-R1 treated as the reasoning models that omit temperature). One honest caveat: modern frontier models blur this line (your "coding heavyweight" models are also reasoning models), so frame the categories as a *deliberate diversity scaffold* rather than a hard taxonomy — which the text essentially already does.

**Prompts (§6.4–§6.5).** The choice of the simplest prompt (Π_ZS-S) for Stage 1, grounded in the predecessor's counter-intuitive finding, is well-argued. The architecture-aware rule matrices (Tables 6.4–6.5) are excellent — they concretely demonstrate that the four planners receive genuinely different, component-traceable rules, which is the scientific heart of the thesis.

---

## Part C — References (Chapter 6)

All 14 citations are already audited and used appropriately: `Elis2025`, `Georgievski2025`, `Georgievski2026`, `Merkel2014`, `Helmert2006`, `RichterWestphal2010`, `Rintanen2012`, `LipovetzkyGeffner2017`, `GnadHoffmann2018`, `Vallati2021`, `Franco2019`, `FoxLong2003`, `McCluskey2017`, `Helmert2009`. The six-generic-rules citation set (`Vallati2021, Franco2019, FoxLong2003, Helmert2009, McCluskey2017`) is consistent with Chapter 3. No new references. ✓

---

## Part D — Figures and tables

| Table | Verdict |
|---|---|
| **6.1** Selected planners | ✅ accurate (winners/baselines correctly attributed). |
| **6.2** Domain structural quantification | ✅ values span the claimed ranges exactly; strong evidence for diversity. |
| **6.3** Selected LLMs | ✅ model IDs consistent with Ch. 5 and `requirements.txt`. |
| **6.4 / 6.5** Architecture-aware rule matrices | ✅ clearly differentiate the four planners; `SCC` is defined in the abbreviations. |
| **6.6** Hardware | ✅ but see E1 (macOS/Docker) and E2 (GPU). |
| **Listing 6.1** config excerpt | ✅ now shows `alpha: 0.25`, `min_mean_gain: 0.0` — consistent with Ch. 4 and your actual code. |

No standalone figures in this chapter (tables + one listing), which is appropriate.

---

## Part E — Smaller findings

**E1 — Hardware is an iMac Pro running macOS; planners run in Docker (note for Threats to Validity).** Docker Desktop on macOS runs Linux containers inside a lightweight VM, which adds a virtualisation layer on top of the host. This does **not** invalidate your results — because all comparisons are *paired* on the same machine, the constant VM overhead cancels out — but given how much you (correctly) emphasise timing precision and the Wilcoxon test's noise sensitivity, it is worth one sentence in the Threats-to-Validity chapter acknowledging the macOS/Docker virtualisation layer and why paired comparisons remain valid.

**E2 — The GPU row in Table 6.6 is irrelevant.** Classical planning is CPU-bound and the LLMs are accessed via API, so the AMD Radeon Pro Vega 64 plays no role. Consider removing the GPU row (or adding a half-sentence that it is unused), so the table reflects only what affects the experiment.

**E3 — §6.4 validity-rate comparison is slightly apples-to-oranges.** You give Π_ZS-S as "79.29% syntactic" and "55.00% semantic", then compare the *other* strategies as "full validity rate" (45.00% / 46.43% / 50.71%). For a clean comparison, also state Π_ZS-S's *combined* (both-valid) rate so all five strategies are compared on the same metric. Minor clarity.

**E4 — Optional cross-reference for α = 0.25.** Listing 6.1 shows `alpha: 0.25` without local explanation; a reader landing here may be surprised by the non-standard value. Consider a parenthetical pointing to Ch. 4's improvement-screening rationale (`\Cref{sec:design:stage2:improvement}`). Optional.

---

## Part F — IAAS guideline check + fixes applied

| Guideline | Status |
|---|---|
| Don't open chapter/section/paragraph with "This" | 🔧 fixed three openings (chapter intro L4; the post-Table-6.1 paragraph L64; the §6.5 paragraph L270). |
| Capitalised, consistent cross-references | 🔧 changed two `Listing~\ref{}` to `\Cref{}` (L251, L445) to match the thesis convention. (Left `Appendix~\ref{}` as-is — safer than `\Cref` for an appendix chapter.) |
| British spelling | ✅ consistent (no American spellings found). |
| Acronyms defined | ✅ incl. `SCC` (in `abbreviations.tex`). |
| "we" / present tense | ✅ appropriate. |
| Tables captioned & referenced | ✅ all six. |
| Consistency with Ch. 4/5 | ✅ α, instances (15, seed 42), Docker limits, hardware, model IDs all match. |

---

## Part G — Changelog

**`content/05-implementation.tex`** (your confirmed Ch. 5 items)
1. CPLEX "22.12" → "22.1.2" (×3: §5.2, Table 5.3, §5.3).
2. DecStar "competed in" → "won the Agile Track of the IPC 2023".

**`content/06-experimental-setup.tex`**
3. L4: "This chapter specifies…" → "The present chapter specifies…".
4. L64: "This selection guarantees…" → "Overall, this selection guarantees…".
5. L270: "This observation motivates…" → "These observations motivate…".
6. L251, L445: `Listing~\ref{…}` → `\Cref{…}`.

---

## Part H — Action items for you

1. **Add §6.8 "Evaluation Metrics"** (Part A) — the one substantive gap. Define coverage, the final global IPC score, PAR10, runtime, plan cost, validity/equivalence rates, and token efficiency. *I'm offering to draft it from your `analysis/` definitions — just confirm.*
2. **Threats to Validity:** add one sentence on the macOS/Docker virtualisation layer (E1).
3. **Table 6.6:** remove or annotate the unused GPU row (E2).
4. **§6.4:** add Π_ZS-S's combined validity rate for an apples-to-apples comparison (E3).
5. **Optional:** cross-reference the α = 0.25 rationale from Listing 6.1 (E4).
6. **Recompile** and skim Tables 6.1–6.6 for placement.

Chapter 6 is in strong shape; the selection methodology is a highlight of the thesis. The evaluation-metrics section is the one thing standing between it and "complete." Ready for **Chapter 7 (Results)** when you are — and note that Ch. 7 will depend directly on the metric definitions from Part A, so adding §6.8 first would make the Ch. 7 review smoother.

---

## Sources used for verification
- IPC 2018 Agile (LAPKT-BFWS-Preference, winner) and IPC 2023 Agile (DecStar-2023, winner) — as cited in the Chapter 5 review.
- Repository cross-check: `requirements.txt`, `config/experiment_config.yaml`, `abbreviations.tex` (local).
- Predecessor validity figures cross-checked against `Markdowns/3. bachelor_thesis_daniel_elis_compressed.md` and the modified Georgievski paper.
