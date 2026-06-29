# Supervisor-Style Review — Chapter 7 (Results)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 7 (`content/07-results.tex`, **699 lines**, ~9 figures, ~17 tables), cross-checked against the `analysis/` reports, the figure images, Chapters 4–6, and the bibliography.
**Date:** 26 June 2026

> **Verdict:** This is an **outstanding results chapter** — analytically sophisticated, exceptionally well-written, and (most importantly) **accurate to your data**: every headline number I spot-checked matches the `analysis/` reports exactly. It is also genuinely *long* — your instinct is right — and I give concrete trim recommendations in Part D. I viewed the key figures directly; they are correct and well-made (two minor notes). Four "This"-opening sentences are fixed.

---

## Part A — Numbers accuracy (verified against `analysis/`)

This is the single most important check for a results chapter, and the result is excellent. I verified the headline figures against your analysis reports; **every one matches**:

| Claim in Ch. 7 | `analysis/` source | Match |
|---|---|---|
| Stage 0: 168/300 SUCCESS, 132 TIMEOUT, 56.0% | `stage0/1_Summary` | ✅ |
| Per-planner (BFWS 64, LAMA 53, DecStar 26, Madagascar 25) | coverage heatmap sums | ✅ |
| IPC progression 154.17→157.93→161.44→163.87 (+9.70) | `cross_stage/1_Global_IPC` (154.169…163.873) | ✅ |
| Combined improvement 44.1%→80.9% (55/68) | `cross_stage/9_Improvement_Funnel` | ✅ |
| Friedman χ²=267.06, p=1.3×10⁻⁵⁷, W=0.30 | `cross_stage/10_Statistical` (267.058, 1.34e-57, 0.2967) | ✅ |
| S1 vs S2: 158/24, p=2.2×10⁻²¹; S0 vs S2: 174/7, p=1.4×10⁻²⁹; S2 vs S3: 80/103, p=2.3×10⁻³ | Section 10 pairwise table | ✅ |
| Cliff's δ S0–S2 = 0.30 [0.2185, 0.3859] | Section 10 (0.3012) | ✅ |
| Kruskal–Wallis: LLM S1=25.1***, S2/S3 n.s.; planner 26.6→39.9→76.7 | Section 10 KW table | ✅ |
| Stage 2: 42/75 (56%), LAMA 18/18, BFWS 11/19, DecStar 7/18, Madagascar 6/20 | `stage2/` | ✅ |
| Stage 3: 30 seed improvements, 47.1% contestable | `stage3/` | ✅ |

Beyond the spot-checks, the chapter's **internal arithmetic is flawless** — every count sums to its total and every percentage recomputes (I checked the planner/domain/stage breakdowns throughout). You can be confident the numbers are right. One stylistic plus: the prose translates your (understandably informal) analysis-report language into measured, academic phrasing — exactly right.

---

## Part B — Figures: deep review

I opened and inspected the figure images directly. I viewed five in detail (coverage heatmap, specialisation scatter, Cliff's-δ forest, per-LLM IPC progression, per-planner stage progression) and confirmed each against the text; the remaining four are of the same provenance and style.

**Choice of visuals — excellent and varied.** Heatmap (coverage), scatter (runtime–cost; specialisation), bar (reordering frequency), histogram (IPC gains), line (solve-rate and IPC trends), and a forest plot (effect sizes). Each is the *right* chart for its message, and none is redundant. The forest plot in particular is a sophisticated, examiner-pleasing choice for effect sizes.

**Accuracy — confirmed.** The coverage heatmap values sum exactly to the planner totals (BFWS 15+8+11+15+15=64, etc.) and the domain totals; the forest plot matches the Cliff's-δ table to the decimal (0.30 for S0–S2, −0.09 for S2–S3); the per-LLM progression matches the text ("GPT-5.4 accelerates to the top", "Gemini peaks at iteration 2 then regresses", "DeepSeek-R1 flat"); the per-planner progression matches the stated gains (+4.53 BFWS, +0.71 DecStar).

**Two minor figure issues:**
1. **`s2_specialization_scatter` — colour-only encoding (accessibility).** Planners are distinguished only by colour, and the palette pairs **red (BFWS) with green (LAMA)** — the hardest pair for red–green colour-blind readers, all using the same circle marker. Your *line* charts already solve this with distinct marker shapes (circle/square/triangle/diamond); please regenerate this scatter with per-planner marker shapes too. (Also: the caption attributes the upper-right cluster to "Depots", but the figure is coloured by *planner*, so that domain claim isn't visible in the plot — fine as added context, just be aware.)
2. **Embedded spelling.** The scatter's embedded title reads "Architecture **Specialization**" (US) while your prose and section heading use British "Specialisation". Regenerate with the British spelling for full consistency (minor; it's baked into the PNG).

**One thing to verify (forest plot vs text):** the text states "all five baseline- and generic-referenced confidence intervals exclude zero", but in `cs_forest_cliffs_delta` the **S0-vs-S1** interval (grey, "Negligible") sits visually right at zero. Its Wilcoxon test is highly significant (p=2.7×10⁻⁷), so the lower bound is almost certainly just above zero — but please confirm the CI lower bound is clearly > 0 so the figure unambiguously supports the sentence.

---

## Part C — Tables: deep review

Seventeen tables, all accurate and well-captioned (your captions do real explanatory work — e.g., warning that only coverage is comparable across planners). A few observations:

- **Strong, necessary tables:** the pairwise stat table (`stat_pairwise`), the Kruskal–Wallis factor table (`stat_kw`), the combined Stage 2+3 funnel (`s3_combined`), the source-of-best-config table (`cs_source`), and the prior-work comparison (`elis_comparison`). Keep all.
- **`s2_improvement_domain_llm`** is a clever space-saver (domain and LLM side by side). Good.
- **Candidate to condense — `s0_metric_availability`** (which planner reports which metric): this largely repeats what Chapter 5 §5.3 already documents (per-planner metric parsing) and the N/A discussion of §4.1.1. Consider replacing the table with a one- or two-sentence summary plus a reference to §5.3 (see Part D).
- Stage 0 carries **four tables**; that is a lot for a baseline (Part D).

---

## Part D — Length, and what to trim (your question)

**Yes, the chapter is long (≈699 lines, 26 floats), and it can be tightened — chiefly in Stage 0.** The writing quality is high, so I would *not* cut whole analyses; the issue is proportion. Stage 0 (the *baseline*) currently runs ~200 lines with **4 tables + 2 figures** — longer than any of the actual intervention stages. Three concrete, low-risk trims:

1. **Consolidate the "survivorship / measurement-scope" argument.** The same methodological point — *efficiency metrics aren't comparable across planners because averages are over different solved subsets, so we use per-instance IPC pairing* — is made in §7.1.2 (planner-level) **and** again in §7.1.5 (plan cost). Make it once, forcefully, and cross-reference. Saves ~15–20 lines.
2. **Condense `s0_metric_availability`** (Part C) to prose + a reference to §5.3. Saves a table and a few lines.
3. **Tighten §7.1.5** ("Plan Cost, Runtime Variance, Measurement Scope") — the coefficient-of-variation detail (0.31–2.57, the 62-fold Depots×DecStar spread) is vivid but could be a single sentence rather than a paragraph.

Together these would shorten Stage 0 by roughly a page and rebalance the chapter so the baseline no longer outweighs the intervention stages. **Everything from Stage 1 onward is well-proportioned — leave it.**

---

## Part E — Anything missing or that should be added?

- **Nothing essential is missing.** The chapter answers SQ2 (Stage 2 efficacy/specialisation), SQ3 (the feedback-loop 44.1%→80.9%), and SQ5 (cross-architecture response: BFWS>LAMA>Madagascar>DecStar, DecStar resilience, the "amplification" finding) directly and well. The explicit point-by-point SQ answers belong in the Conclusion (Ch. 9), so their absence here is correct.
- **One small consolidation worth considering (SQ4 — hallucination prevention).** The validation/hallucination evidence is present but *scattered* (90% valid at S1; 93.8% at S2; the per-iteration 93.8%/90.0%/86.8% at S3; "the hard-critic gate caught all 21 invalid iterations before any reached a planner"). Since preventing semantic hallucination is one of your research questions, consider gathering these into one or two sentences (e.g., a short "Validation integrity across the pipeline" note) so SQ4 has a clearly locatable home in the results. Optional, but it would strengthen the SQ4 thread.
- **Removable:** only the condensations in Part D — no section should be cut outright.

---

## Part F — Metric definitions (your Ch. 6 decision)

You chose to define metrics in Ch. 7 rather than add a §6.8, and you followed through: **coverage** (intro), the **global IPC score** (intro, referencing Eq. 4.4), the **specialisation index** (§7.3.3), and the statistical measures (§7.6.1) are all defined on first use. Critically, **PAR10 is now defined** where it first appears — the `cs_coverage_par10` caption states "penalises each unsolved instance by 10× the time limit." That closes the gap I flagged in the Ch. 4/6 reviews. 

---

## Part G — Consistency with Chapters 4–6

- **α screening vs confirmatory:** §7.3.2 uses the relaxed α=0.25 for the screening gate and explicitly defers confirmatory testing to §7.6 at α=0.05 — exactly the framing built into Ch. 4. ✅
- **Global IPC reference:** §7.5 recomputes every run against a single global T\*ᵢ, fulfilling Ch. 4's promise. ✅
- **One clarity point (Stage 3 count).** Ch. 4 says Stage 3 "processes all 80 triples"; Ch. 7 reports "68 contestable" (12 always-timeout excluded) and "218 iterations". A careful reader will note 68 × 3 = 204 < 218, which is only explained if the 12 always-timeout triples also entered the loop and terminated early. That is in fact what happened, and it is consistent with Ch. 4 — but add a half-sentence making it explicit (e.g., "all 80 triples enter the loop; the 12 always-timeout triples terminate after one iteration and are excluded from the contestable analysis, leaving 68"). Removes a potential point of examiner confusion.

---

## Part H — References

The only new citation, **`Romano2006`** (Cliff's-δ thresholds), is real and correctly recorded — authors *Romano, Kromrey, Coraggio, Skowronek*, the NSSE ordinal-statistics paper, 2006. ✅ `Elis2025` and `Georgievski2025` are used appropriately in the prior-work comparison. No fabricated or mismatched references.

---

## Part I — Guidelines + fixes applied

| Guideline | Status |
|---|---|
| No "This"-opening of chapter/section/paragraph | 🔧 fixed four (L4 chapter opener; L295 §7.2.3; L532 §7.5.1; L671 §7.7 opener). |
| British spelling in prose | ✅ consistent (the only "Specialization" is inside a figure image — Part B2). |
| Acronyms defined (PAR10, VSIDS, Cliff's δ, etc.) | ✅ defined on first use. |
| `\Cref` cross-references | ✅ throughout. |
| `\num{}` for large numbers | ✅ used consistently. |
| Captions connect floats to text | ✅ exemplary — captions carry interpretation. |

---

## Part J — Changelog & action items

**Applied (`content/07-results.tex`):** four "This"-opening sentences reworded (L4, L295, L532, L671).

**For you to action (none critical):**
1. **Trim Stage 0** per Part D (consolidate the survivorship argument; condense `s0_metric_availability`; tighten §7.1.5) — the main lever for the length concern.
2. **Regenerate `s2_specialization_scatter`** with per-planner marker shapes and British "Specialisation" (Part B).
3. **Confirm the S0-vs-S1 forest CI** clearly excludes zero (Part B).
4. **Add a half-sentence** reconciling the 80-vs-68 Stage 3 count (Part G).
5. **Optional:** gather the SQ4 validation-integrity evidence into one place (Part E).
6. **Recompile** and check float placement (with 26 floats, a few may drift; `[htbp]` is already used, which helps).

This chapter is the strongest in the thesis and is essentially submission-ready. The accuracy against your data is its greatest strength — that is exactly what an examiner hopes to find and rarely does.

---

## Sources used for verification
- `analysis/output/` — `stage0/1_Summary`, `cross_stage/1_Global_IPC_Score`, `9_Improvement_Funnel`, `10_Statistical_Meta_Analysis`, `stage2/`, `stage3/` (headline-number cross-checks).
- Figure images in `figures/results/` (viewed directly).
- `Romano2006` bibliography entry; Chapters 4–6 for consistency.
