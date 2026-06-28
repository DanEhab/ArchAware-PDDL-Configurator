# Supervisor-Style Review — Chapter 5 (Implementation)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 5 (`content/05-implementation.tex`, 565 lines), cross-checked against Chapter 4, the repository (`requirements.txt`, planner code/config), and the bibliography.
**Date:** 26 June 2026
**Note:** First-time review. Chapter 5 was also lightly touched during the Chapter 4 coordination pass (one sentence added to §5.1.2).

> **Read order.** Part A = fit as a "Realisation" chapter and the Ch. 4 ↔ Ch. 5 split. Part B = technical accuracy (this is where the two recommendations live: a CPLEX version number and a DecStar claim you can strengthen). Part C = references. Part D = figures/tables/listings. Part E = guidelines + what I fixed. Part F = changelog. Part G = your action items.

---

## Overall assessment

This is a **strong, professional implementation chapter** and an excellent companion to the revised Chapter 4. It does exactly what the IAAS "Realisation of Solution" guideline asks—*how* the design is practically realised—and it opens by stating that split explicitly ("Chapter 4 specified *what* … the present chapter explains *how*"). The planner-integration section is the highlight: detailed, honest provenance (exact repositories, build steps, and invocation commands) for four genuinely awkward legacy planners.

Two things stand out as markers of quality:

1. **It is accurate to the repository.** Every dependency version in §5.1.5 matches `requirements.txt` exactly (openai ≥ 1.75, anthropic ≥ 0.52, google-generativeai ≥ 0.8.5, PyYAML ≥ 6.0, pandas ≥ 2.2, numpy ≥ 2.0, scipy ≥ 1.13, statsmodels ≥ 0.14, matplotlib ≥ 3.9, seaborn ≥ 0.13, tenacity ≥ 9.0). That level of fidelity is exactly what an examiner hopes to find.
2. **The planner facts check out.** I verified externally that LAPKT-**BFWS**-Preference *won* the IPC 2018 Agile Track (as you state), and the LAMA `lama-first` alias correction over the predecessor's manual proxy configuration is a real, well-explained methodological improvement.

I fixed three small things (provider/SDK wording, a duplicated paragraph, one spelling). Two items are **recommendations you should action** (a CPLEX version number, and a DecStar claim you can legitimately strengthen) — neither is auto-changed because both are factual details about your own setup/competition results that you should confirm.

---

## Part A — Fit as a "Realisation" chapter, and the Ch. 4 ↔ Ch. 5 split

After last round's coordination, the two chapters now divide cleanly:

- **Chapter 4** = abstract design (stages, data architecture, validation logic, safeguard rationale).
- **Chapter 5** = realisation (codebase, Docker, planner builds, VAL, LLM provider layer).

The opening two sentences make this explicit, and the chapter consistently links implementation back to the design (e.g., "the cross-cutting concerns described in §4.7", "the V2 stage of the validation pipeline (§4.6)"). I checked for left-over duplication after the Ch. 4 trims: none remains. The mechanics that were removed from Chapter 4 (thread-safe CSV writer, checkpoint hash-set, heartbeat, `--memory-swap`, the `N/A` sentinel) now live **only** here, in their proper place (Table 5.1, §5.2). Good.

---

## Part B — Technical accuracy

**B1 — CPLEX version number (please verify; likely a typo). 🟠**
The chapter cites "IBM CPLEX 22.12" / "CPLEX Studio 22.12" in three places (§5.2 intro, Table 5.3, §5.3 DecStar build), but the installer you name is `cplex_studio2212.linux_x86_64.bin`. In IBM's versioning, `2212` denotes **CPLEX Optimization Studio 22.1.2** (22.1.0 → `2210`, 22.1.1 → `2211`, 22.1.2 → `2212`); there is no release "22.12". So "22.12" is almost certainly meant to be **22.1.2**. Please confirm and correct all three occurrences. *(Not auto-changed: it's a version you installed and can verify in seconds.)*

**B2 — DecStar: you can strengthen "competed in" to "won". 🟢**
You write that DecStar "competed in the Agile Track of the IPC 2023." That is true but understated: **DecStar-2023 *won* the Deterministic Agile Track of IPC 2023** (Gnad, Torralba, Shleyfman). Since you already (correctly) say BFWS "won" the IPC 2018 Agile Track, strengthening DecStar to "won the Agile Track of the IPC 2023" would make the planner-selection narrative both stronger and symmetric. Please confirm against the official IPC 2023 results / the AI Magazine IPC 2023 report, then upgrade the wording. *(Not auto-changed: it's a competition-result claim you should own; "competed in" is safe as-is.)*

**B3 — Everything else checks out.** The Docker resource flags (`--cpus`, `--memory`, `--memory-swap`) match the §4.7 safeguards; the per-planner metric coverage is internally consistent (LAMA/DecStar report all seven metrics; BFWS records states-evaluated and peak-memory as `N/A`; Madagascar records the four search/memory metrics as `N/A`)—and this matches the `N/A`-not-`0` rule in §4.1.1. The five domains in the directory tree (barman, depots, ricochet-robots, snake, visitall) match the rest of the thesis. The four LLMs (GPT-5.4, DeepSeek-R1, Claude Opus 4.6, Gemini 3.1 Pro) match Chapter 1 and `requirements.txt`.

---

## Part C — References (Chapter 5)

No new references; all eight are already audited and used appropriately:

| Citation | Where | Appropriate? |
|---|---|---|
| `RichterWestphal2010`, `Helmert2006` | LAMA / Fast Downward (§5.3) | ✅ |
| `LipovetzkyGeffner2017` | BFWS (§5.3) | ✅ |
| `GnadHoffmann2018` | DecStar / decoupled search (§5.3, ×2) | ✅ |
| `Rintanen2012` | Madagascar / SAT planning (§5.3) | ✅ |
| `HoweyLongFox2004` | VAL (§5.4) | ✅ |
| `Merkel2014` | Docker (§5.2) | ✅ |
| `Elis2025` | LAMA-config correction; Madagascar binary provenance (§5.3) | ✅ |

---

## Part D — Figures, tables, listings

| Float | Verdict |
|---|---|
| **Fig 5.1** (sequence diagram) | ✅ Clear; short caption for the List of Figures; steps 1–11 are coherent. Minor: it shows the VAL container (V2) but folds V1/V3/V4 into the orchestrator's local actions — fine, and the surrounding text makes that explicit. |
| **Table 5.1** (shared modules) | ✅ Now also covers heartbeating + terminal-output logging (added last round). |
| **Table 5.2** (stage modules) | ✅ `\multirow` layout reads well. |
| **Table 5.3** (Docker images) | ✅ accurate (apart from the CPLEX version, B1). |
| **Table 5.4** (LLM→provider mapping) | ✅ consistent with the corrected provider/SDK wording. |
| **Listings 5.1–5.x** | ✅ The captioned listings (dir tree, output protocol, `docker run`, LAMA build) are referenced from the text. The short invocation snippets (BFWS/DecStar/Madagascar/VAL) are intentionally uncaptioned inline code — acceptable; optionally caption them for uniformity. |

---

## Part E — IAAS guideline check + fixes applied

| Guideline | Status |
|---|---|
| Don't open chapter/section/paragraph with "This" | ✅ none (the chapter opens "The experimental pipeline designed in …"). |
| Capitalised cross-references | ✅ `\Cref` throughout. |
| British spelling | 🔧 one fix — "JSON-serializable" → "JSON-serialisable" (everything else was already British). |
| Acronyms / `\gls` | ✅ LLM/PDDL/IPC/SAT/BFWS/LAMA via glossary; SDK/API/YAML/UUID used conventionally. |
| "we" / present tense | ✅ appropriate. |
| Accuracy to artefacts | ✅ dependency versions match `requirements.txt`. |

**Fixes applied this pass:**
1. §5.5 opening: "four LLMs from **three** different providers, each accessed through its **native** SDK" → "four LLMs spanning **four** providers (OpenAI, DeepSeek, Anthropic, Google), accessed through **three** official Python SDKs, since DeepSeek is reached through the OpenAI SDK." (The old wording miscounted providers and was inaccurate for DeepSeek.)
2. Removed a **duplicated paragraph**: the DeepSeek-inherits-`OpenAIProvider` explanation appeared twice (before and after Table 5.4). Consolidated into one place, keeping the concrete base-URL/key detail.
3. "JSON-serializable" → "JSON-serialisable" (British consistency).

---

## Part F — Changelog

**`content/05-implementation.tex`**
1. §5.5 intro sentence reworded for provider/SDK accuracy (4 providers, 3 SDKs).
2. §5.5.1: enriched the `DeepSeekProvider` sentence with the base URL/key and **deleted** the redundant post-table paragraph that repeated it.
3. §5.4.1: "JSON-serializable" → "JSON-serialisable".

*(Also from last round: one sentence added to §5.1.2 so terminal-output logging is documented here rather than in Ch. 4.)*

**Deliberately not changed (your factual calls):** the CPLEX version number (B1) and the DecStar "competed in" → "won" upgrade (B2).

---

## Part G — Action items for you

1. **Fix the CPLEX version** (B1): change "22.12" → "22.1.2" in all three places, after confirming against your installer (`cplex_studio2212` = 22.1.2).
2. **Strengthen the DecStar claim** (B2): "competed in" → "won the Agile Track of the IPC 2023", once you confirm via the official IPC 2023 results.
3. **Optional:** caption the short invocation listings for uniformity with the other listings.
4. **Recompile** (done) and skim Fig 5.1 and the tables for placement.

Chapter 5 is in very good shape — after the two factual confirmations above, it's submission-ready. Ready for **Chapter 6 (Experimental Setup)** whenever you are; I'll check the evaluation-metrics definitions there (including where **PAR10** and the **α = 0.25 / 0.05** distinction should be defined, which connects back to Chapters 4 and 7).

---

## Sources used for verification
- IPC 2018 Agile Track — LAPKT-BFWS-Preference (winner): https://edoc.unibas.ch/68740/ · https://nirlipo.github.io/publication/frances-2018-best/
- IPC 2023 (DecStar-2023, Agile Track) — *The 2023 International Planning Competition*, AI Magazine: https://onlinelibrary.wiley.com/doi/10.1002/aaai.12169 · https://ipc2023-classical.github.io/
- Repository cross-check: `requirements.txt`, `config/experiment_config.yaml`, `experiments/arch-aware/` (local).
