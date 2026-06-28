# Supervisor-Style Review — Chapter 4 (Design of the Experimental Pipeline)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 4 (`content/04-design.tex`, 913 lines), cross-checked against Chapters 1–3 and the bibliography.
**Date:** 26 June 2026
**Note:** First-time review (no prior supervisor comments flagged).

> **Read order.** This chapter is technically strong, so the value here is in a few methodological points (Part B) and a structural question (Part A), not error-hunting. Part A = structure/IAAS fit. Part B = technical accuracy & the methodological flags (α, the IPC reference time, PAR10). Part C = references. Part D = figures/tables. Part E = guidelines. Part F = changelog. Part G = your action items.

---

## Overall assessment

This is a **rigorous, well-engineered design chapter** — the strongest evidence so far that the methodology is sound. The four-stage ablation is cleanly motivated ("each stage adds exactly one variable"), the figures communicate the architecture well, and — importantly — **every quantitative claim reconciles**:

| Claim | Check |
|---|---|
| Stage 0 runs = 5×4×15 = 300 (Eq 4.1) | ✅ (75 domain–instance pairs × 4 planners) |
| Stage 1 API calls = 4×5 = 20; planner runs ≤ 4×5×4×15 = 1,200 (Eq 4.2) | ✅ |
| Stage 2 LLM calls = 4×5×4 = 80 (Eq 4.3); 20 per LLM | ✅ |
| Stage 3 runs ≤ 80×3×15 = 3,600 (Eq 4.7); 20 triples per LLM | ✅ |
| V4: 9 components × 2 flags = 18 flags/domain | ✅ |

It is also **consistent with Chapters 1–3**: four planners (BFWS, LAMA, DecStar, Madagascar), five domains, four LLMs, the four-level validation pipeline (V1–V4), the three validity properties, and the "extends the three-stage `Georgievski2025` pipeline" claim all match. The earlier "official validator" wording is correctly now "standard plan validator used in the IPC." No new references are introduced, and all five citations used here (`Kambhampati2024`, `Georgievski2025`, `Elis2025`, `Vallati2021`, `HoweyLongFox2004`) are already audited and used appropriately.

**What needs your attention** is a small set of *methodological* points an examiner will likely probe — chiefly the **α = 0.25** significance level and the **two different definitions of the IPC reference time T\*** — plus one **undefined metric (PAR10)** and a **structure question** (how much implementation detail belongs in a "Design" chapter). None are errors; they are judgement calls I did not change for you, because they concern your methodology. Details below.

I fixed four guideline issues (paragraph/chapter openings with "This").

---

## Part A — Structure and IAAS "Design of Solution" fit

The IAAS guideline frames this section as the **abstract design** ("architectural design, an algorithm, or another form"), with implementation details belonging to the separate **Realisation/Implementation** chapter (your Ch. 5).

Chapter 4 is excellent on the abstract design (the staged ablation, the validation pipeline, the improvement test, the safeguards). However, it also contains a fair amount of **implementation-level detail** that arguably belongs in Ch. 5:

- exact CSV **column schemas** (Tables 4.1–4.3) and file names (`planner_execution_data.csv`, `pddl_diff_metrics.csv`, …);
- **threading primitives** (`ThreadPoolExecutor`, `threading.Lock`, mutex, $O(1)$ hash-set checkpointing);
- **logging mechanics** (`TeeLogger`, `pipeline_heartbeat.log` "every 60 seconds", error-dump files);
- Docker flags (`memory-swap` set equal to `memory`).

**Recommendation (your call, not changed):** consider keeping Ch. 4 at the level of *what* the pipeline does and *why* (stages, data **architecture**, validation logic, safeguards) and moving the *how* (threading, exact filenames/log mechanics, container flags) to Ch. 5. The data **schemas** themselves are defensible in a design chapter as "data architecture," so they can stay if you prefer. The key is to avoid Ch. 4 and Ch. 5 repeating the same implementation detail. If your supervisor already approved this split, it's fine — but be ready to explain why the boundary sits where it does.

---

## Part B — Technical accuracy, internal consistency, and methodological flags

**B1 — α = 0.25 significance level (most important).**
The improvement test (Condition A, L456) uses a Wilcoxon signed-rank test at **α = 0.25**, "relaxed to account for LLM volatility." This is *far* above the conventional 0.05, and an examiner will almost certainly ask about it: at α = 0.25 you accept up to a 25% false-positive rate, so "statistically significant improvement" claims rest on a weak threshold. It is *defensible* as an exploratory, screening criterion (especially combined with Conditions B and C), but you should:
1. **Justify it explicitly** where it's introduced (you have one clause; expand it), and again in the **Threats to Validity** chapter (conclusion validity).
2. **Report the actual p-values and effect sizes**, not just the binary verdict, so readers can judge for themselves.
3. Make sure the **same α is used and stated consistently** in Ch. 6/7 (I'll check this when we review those).
*(Not changed — this is your methodological decision; I'm flagging it so it's deliberate and defended, not silently inherited.)*

**B2 — Two different definitions of the IPC reference time T\* (clarify).**
- In Stage 2 (L433), T\*ᵢ is "the fastest wall-clock runtime achieved by the same planner on instance i across **all configurations from all completed stages**."
- In Stage 3 (L649), "the reference time T\*ᵢ considers **only the baseline and current iteration's** runtimes."

So Eq 4.4 is computed against **different reference sets** in different stages. Within Stage 3's loop that's reasonable (a local verdict), but it means a "Stage 2 IPC score" and a "Stage 3 IPC score" are **not on the same scale**, which complicates any cross-stage IPC comparison in Ch. 7. Please either (a) make T\* consistent, or (b) state explicitly that the two scores serve different purposes (per-stage screening vs. cross-stage comparison) and keep cross-stage comparisons to a consistently-recomputed score. Worth one or two sentences.

**B3 — PAR10 is used but never defined.**
PAR10 appears in Ch. 4 (L220 "PAR10 ratios", L890 "for PAR10 … computation") but I could not find a definition anywhere in the written chapters (it is only mentioned in a stray comment in the unused `05-realisation.tex` placeholder). Define **PAR10** (Penalised Average Runtime with factor 10 — timeouts counted as 10× the time limit) where you introduce evaluation metrics (most naturally Ch. 6), and ideally add a forward reference at first use in Ch. 4. *(Not added by me — it's content that belongs with your metric definitions; I'll confirm it lands when we review Ch. 6.)*

**B4 — IPC score formula (minor, verify comparability).**
Eq 4.4, `Score = 1 / (1 + log₁₀(Tᵢ(C)/T\*ᵢ))`, is a standard IPC-agile-style score and behaves correctly (1 at best time, →0 as it slows). Just confirm it is the **same** formula `Georgievski2025`/`Elis2025` used, since you compare against their results in Ch. 7; if they used a different agile-score variant, note it.

**B5 — "Random seeds" (trivial).**
L131 lists "random seeds" among centralised reproducibility parameters, but the design is fully deterministic (LLM T = 0.0, deterministic planners). If nothing is stochastic, "random seeds" is vestigial — consider removing it or clarifying what it seeds.

Everything else I checked is internally consistent: the per-stage run counts, the work-queue sizes (75 pairs), the phase labels (A–E) matching Figure 4.1, the 9 V4 components matching Table 4.4 and the Stage 1 text, and the improvement conditions A/B/C matching Eq 4.6.

---

## Part C — References (Chapter 4)

No new references. All five citations are already audited and are used appropriately:

| Citation | Where | Appropriate? |
|---|---|---|
| `Kambhampati2024` | LLM-Modulo framework (L124, L514) | ✅ |
| `Georgievski2025` | planner-agnostic baseline; 3-stage pipeline; non-normality (L293, L459, L796, L871) | ✅ |
| `Elis2025` | Wilcoxon/non-normality; IPC protocol (L459, L871, L880) | ✅ |
| `Vallati2021` | architecture-dependent structural sensitivity (L489) | ✅ |
| `HoweyLongFox2004` | VAL (L810) | ✅ |

---

## Part D — Figures and tables

| Float | Verdict |
|---|---|
| **Fig 4.1** (pipeline overview) | ✅ Clear; uses a short caption for the List of Figures; phase labels A–E match the text. |
| **Table 4.1** (planner CSV, 17 cols) | ✅ Matches "columns 9–16 = metrics" reference (L218). |
| **Table 4.2** (LLM-gen CSV, 17 cols) | ✅ Consistent with the V1–V4 `Passed_*` flags described in the text. |
| **Listing 4.1** (general prompt) | ✅ Verbatim; American spelling ("optimize") is correct to keep (it's the literal prompt). |
| **Listing 4.2** (arch-aware template) | ✅ Five sections match the "Sections 1–4 / Section 5" description. Verbatim spelling OK. |
| **Listing 4.3** (Stage 3 template) | ✅ Consistent with the four-part assembly described after it. |
| **Eqs 4.1–4.7** | ✅ All arithmetic correct; notation consistent with Ch. 2. |
| **Table 4.3** (Stage 3 final CSV, 14 cols) | ✅ |
| **Fig 4.2** (validation pipeline) | ✅ V1–V4 with reject paths; `\dingcheck` is defined. |
| **Table 4.4** (V4 components, 9 rows) | ✅ 9 components × 2 flags = 18, matches L858. |

One **TOC consistency** note (not a float): the chapter toggles `tocdepth` (1 at the start, 2 before §4.6, back to 1 for §4.7). The effect is that the Table of Contents shows subsections **only** for §4.6 (V1–V4) and hides the subsections of every other section. That looks inconsistent — consider either showing all subsections or none. (Left as-is since it's a deliberate formatting choice.)

---

## Part E — IAAS guideline check

| Guideline | Status | Notes |
|---|---|---|
| Don't open a chapter/section/paragraph with "This" | 🔧 | **Four** instances reworded (L7 chapter opener, L293, L485, L796). No others remain. |
| Title of design section depends on content | ✅ | "Design of the Experimental Pipeline" is apt. |
| Capitalised cross-references | ✅ | `\Cref` used throughout for Fig./Table/Eq./Sec. |
| Consistent British spelling | ✅ | centralise/artefact/behaviour/rigour/penalise (verbatim prompt listings keep US spelling, correctly). |
| Acronyms defined / `\gls` | ✅ | LLM/PDDL/IPC/SAT via glossary. **Exception:** PAR10 (Part B3). |
| Figures/tables referenced from text & captioned | ✅ | Every float is introduced before it appears. |
| "we" / present tense | ✅ (acceptable) | Mix of "we" and impersonal description, appropriate for a design chapter. |
| No contractions | ✅ | Body clean (contractions only inside verbatim prompts / cited titles). |

---

## Part F — Changelog (edits applied)

**`content/04-design.tex`** — four paragraph/chapter openings reworded to avoid leading "This":
1. L7: "This chapter presents the design…" → "The present chapter describes the design…"
2. L293: "This design intentionally provides no architecture-specific guidance…" → "By design, the prompt provides no architecture-specific guidance…"
3. L485: "This cross-testing protocol serves two purposes:" → "The cross-testing protocol serves two purposes:"
4. L796: "This four-level pipeline extends…" → "The four-level pipeline extends…"

**Deliberately not changed** (methodology/judgement — your decisions): α = 0.25 (B1), the T\* definitions (B2), PAR10 definition (B3), the design/implementation boundary (Part A), the `tocdepth` toggles (Part D), "random seeds" (B5).

---

## Part G — Action items for you

1. **Defend α = 0.25** (B1): expand the justification in-text, report p-values + effect sizes, and address it under conclusion validity in the Threats chapter. Highest-priority item.
2. **Reconcile / clarify the two T\* definitions** (B2) so cross-stage IPC scores are comparable or clearly distinguished.
3. **Define PAR10** with your evaluation metrics (B3) — I'll verify placement when we review Ch. 6.
4. **Decide the design vs. implementation boundary** (Part A): move the lowest-level mechanics to Ch. 5 if you want a cleaner "abstract design," or keep and justify.
5. **TOC depth** (Part D): make subsection visibility consistent across the chapter.
6. **Minor:** confirm the IPC formula matches the predecessor's (B4); remove/clarify "random seeds" (B5).
7. **Recompile** (you've done this) and skim the rendered Figures/Tables once for placement.

When you're ready, we move to **Chapter 5 (Implementation)** — where I'll expect the threading/Docker/logging detail to live, and I'll check it against this chapter so the two don't contradict or needlessly repeat.

*No external sources were needed for this chapter (no new references). Cross-checks were against your Chapters 1–3 and the audited `bibliography.bib`.*
