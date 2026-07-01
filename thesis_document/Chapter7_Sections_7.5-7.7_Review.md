# Supervisor Review — Chapter 7, Sections 7.5–7.7 (Cross-Stage, Statistical Validation, Prior Work)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration · Youssef · University of Stuttgart (IAAS)
**Scope:** §7.5 Cross-Stage Comparative Analysis, §7.6 Statistical Validation, §7.7 Comparison with Prior Work — `content/07-results.tex`, lines 471–671.
**Cross-checked against:** the `cross_stage` analysis folder (Sections 1–13, all tables/CSVs), `Section10_Statistical_Report.md`, `Section11_Elis_Comparison_Report.md`, `Section13_Key_...Conclusions.md`, the Elis thesis and Georgievski paper markdowns, both figures (viewed directly), `bibliography.bib`, and the IAAS guidelines.
**Mode:** changes applied directly to the `.tex`, length-conscious. Recompile to refresh.

---

## Overall verdict — rating 9 / 10

This is the analytical high point of the chapter, and it is now accurate to your data. §7.6 in particular is a genuine strength: a bachelor thesis that runs Shapiro–Wilk → Friedman → Bonferroni-corrected Wilcoxon → Nemenyi → Cliff's δ with bootstrap CIs → Kruskal–Wallis, and then *honestly reports the one null result* (Stage 2 ≈ Stage 3), is doing exactly what an examiner hopes to see. I verified all 26 statistics in §7.6 against `Section10` — every one matches, including the awkward ones. §7.5's IPC/coverage/PAR10/runtime numbers likewise check out against the CSVs.

Three real errors were hiding in the prose, all now fixed: two inherited number mistakes in §7.5's validation paragraph, and one factually wrong (and internally contradictory) claim in the §7.7 comparison table that also happened to understate prior work your supervisor co-authored. Details below. The score reflects an excellent, near-submission-ready block with a few residual items — chiefly that the same two wrong numbers still live in your `Section13`/`stage3` source files, and one small representation inconsistency.

One correction to my own earlier read: I first thought §7.7 ended on a bare table with no discussion. **It does not** — that was an artifact of a read cutting off at the page break. §7.7 has two solid closing paragraphs (attribution of the validity-vs-improvement leaps, and a well-judged "this is not a controlled experiment" caveat that bridges to \Cref{ch:threats}). No closing paragraph was added.

---

## Part A — Changes applied to `07-results.tex`

| # | §/line | Change | Why | Severity |
|---|---|---|---|---|
| **A1** | §7.5 L564 | Stage 3 loop-validity **"90.0%, 86.8%" → "91.3%, 90.8%"** | The granular per-LLM table `G_T16_Part1` aggregates to 93.8 / **91.3** / **90.8**% (Loop 2 = 63/69, Loop 3 = 59/65). The 90.0/86.8 figures trace only to `Section13`/`stage3` prose and reproduce from no source table. | **Real error** |
| **A2** | §7.5 L564 | **"21 invalid Stage 3 iterations" → "17"** | `G_T16_Part1` gives 5 + 6 + 6 = **17** invalid Stage 3 iterations. 21 is the *all-stage* invalid total (S1 + S2 + S3), misattributed to Stage 3 alone. | **Real error** |
| **A3** | §7.7 table L664 | Significance-testing cell **"$\chi^2$ only" → "Non-parametric + logistic regression"** | "χ² only" is factually wrong *and* contradicts your own design.tex L457 ("both Elis and Georgievski … adopted non-parametric tests"). The Elis thesis actually used logistic regression, Shapiro–Wilk, Mann–Whitney U, **Friedman, and Nemenyi** (Elis MD L1565–2026). The old cell understated prior work co-authored by your supervisor. | **Real error / contradiction** |
| **A4** | §7.7 L644 | Intro: **"semantic validity rate near 49%" → "overall validity rate"**, and co-cited **Georgievski2025** ("also published as \cite{Georgievski2025}") | 49% = 343/700 *full* (syntactic + semantic) validity; semantic-alone was 350/700. And the chapter intro (L12) promises the findings will be positioned relative to Elis2025 **and Georgievski2025** — the latter was previously never cited in §7.7. | Precision + fulfils intro promise |
| **A5** | §7.5 L500 | **"grow roughly sevenfold per stage" → "grow several-fold at each stage"** | Only the S1→S2 token jump is ~7×; S2→S3 is ~3×. "Sevenfold per stage" overstated the second step. | Minor |
| **A6** | §7.7 L671 | **"one domain (Barman)" → "two domains (Barman and VisitAll)"** | Your verification of the Elis selection (IPC 2014 agile domains: barman … visit-all) confirms VisitAll overlaps too, so the domain overlap is two, not one. Planner overlap is correctly just Madagascar. | **Real error** |

Post-edit checks: braces balance (690/690), all cross-reference labels resolve (`ch:threats`, `ch:introduction`, every `sec:`/`tab:`/`fig:`), no contractions, no "This/These"-opened paragraphs, British spelling consistent. No LaTeX breakage; your recompile will pick up the co-citation.

---

## Part B — Section-by-section

### §7.5 Cross-Stage Comparative Analysis — accurate, two inherited errors fixed

Every headline verified against the CSVs: the 7,350-run total; the CS progression 154.17→157.93→161.44→163.87 (+9.70) and SC 123.68→130.36 (+6.68); the marginal +3.76/+3.51/+2.44; the per-planner gains (BFWS +4.53, LAMA +3.04, DecStar +0.71, Madagascar +2.30); the source-of-best table (117+3+14+52+46+68 = 300 ✓, 180 = 98.4% of 183 solvable); coverage +15/132 = 11.4%; the full PAR10 table; runtime −63.7% (Madagascar S3) and the +32%/+23% generic *slowdowns*. All correct. The "amplification" claim (planner gap widens across stages) is well supported by the Kruskal–Wallis planner-H climb (26.6→39.9→76.7).

The only defects were the two validation numbers in §7.5.4 (A1, A2), now fixed. **Figures/tables:** the four chosen artefacts (progression table, per-planner progression figure, source-of-best, coverage/PAR10) are the right four and non-redundant; `cs_ipc_progression_planner` is accurate and uses distinct marker shapes (colour-blind-safe). I did **not** add the improvement-funnel table — the 44.1%→80.9% figure it would support is already carried by the cross-reference to §7.4's `s3_combined`, and the chapter is long.

> **Flag for you (not a thesis edit):** the wrong 90.0/86.8/21 also appear in `Section13` (Obs 17) and your `stage3` key-observations file. The thesis is now correct, but you should fix those source files (or check the script that generated them) so nothing downstream re-inherits the error.

### §7.6 Statistical Validation — the strongest subsection; one softening

All 26 statistics verified against `Section10`: Shapiro–Wilk (W 0.38–0.69, all p<10⁻²²); Friedman χ²=267.06, p=1.3×10⁻⁵⁷, W=0.30; the mean ranks; the full pairwise table (counts, Wilcoxon p, Cliff's δ, Nemenyi) to the decimal; Nemenyi CD=0.27; and every Kruskal–Wallis cell with its significance stars. The handling of the S2-vs-S3 tension (Wilcoxon flags it, Nemenyi does not, δ negligible) is honest and correct.

The one item I changed: the sentence claiming all five CIs "exclude zero, so the improvements are robust." Literally true, but the S0-vs-S1 interval clears zero by only **0.0024** and its effect is **Negligible** — the forest plot (which I viewed) shows it sitting on the axis. I softened it to distinguish the four small-effect comparisons (which clear zero comfortably) from the marginal generic one, so the "robust" framing now attaches only to the meaningful gains. Table/figure selection is ideal; the forest plot is an examiner-pleasing choice and matches the CSV to the decimal.

### §7.7 Comparison with Prior Work — numbers right, one real error fixed, promise fulfilled

The comparison figures all verify (49% = 343/700, 93% = 93/100, 80.9% = 55/68, the 14–26% band). The two fixes were the "χ² only" cell (A3 — the important one) and the intro precision + Georgievski co-citation (A4). The existing two closing paragraphs are strong: they correctly attribute the validity leap partly to model generation and the improvement leap to methodology, and then concede — rightly — that the cross-thesis comparison is *not* controlled and that the real causal evidence is the internal S1-vs-S2 ablation. That is exactly the right intellectual posture and it bridges cleanly to \Cref{ch:threats}.

---

## Part C — Residual items (your call; none blocking)

1. **Overlap claim (L671) — RESOLVED (now A6).** You supplied the Elis selection (planners: SIW, SIW-then-BFSF, Mercury, Madagascar-pC, Fast Downward; domains: barman, genome-edit-distances, thoughtful, transport, visit-all). The domain overlap is **two** (Barman + VisitAll, both IPC 2014), now corrected in the thesis. Planner overlap is confirmed as just Madagascar (LAMA is a distinct Fast Downward configuration from Elis's; BFWS ≠ SIW).
2. **Minor representation inconsistency:** the prior-work improvement rate is written as "~14–26%" (intro + table) but "~20%" in the L669 closing. Both are defensible (≈20% summarises the band), but for polish you could use one form. Left as-is.
3. **Cosmetic only:** the corrected table cell (L664) has leftover alignment spaces in the source after "logistic regression" — invisible in the rendered table, so no action needed unless you like tidy source.
4. **Out of scope (as you instructed):** `s2_specialization_scatter.png` spelling/markers — untouched.

---

## Part D — Guidelines & references

Guidelines: clean throughout §7.5–7.7 — no contractions, all floats `\Cref`-referenced and capitalised, British spelling consistent, `\num{}`/`\gls{}` used, no demonstrative-opened paragraphs. References: after A3–A4, §7.7 cites both `Elis2025` (correctly, as the study it extends) and `Georgievski2025` (the published version), matching the chapter-intro promise; `Romano2006` in §7.6 is correct. No fabricated or broken citations.

### Verification note
All numbers re-checked against the `cross_stage` CSVs; the three corrected items (A1–A3) were verified directly against `G_T16_Part1_Validation_Rates.csv`, the Elis thesis markdown (L1565–2026), and `design.tex` L457. Both figures opened and inspected. Where I could not verify from the repo (the planner/domain overlap of L671), I have flagged it rather than assert it.

### Sources
- `analysis/output/cross_stage/` — Sections 1 (IPC), 2 (Coverage), 3 (Runtime), 4 (`G_T16_Part1`), 9 (Funnel), 10 (`Section10_Statistical_Report` + tables), 11 (`Section11_Elis_Comparison` + `G_T41/G_T42`), 13 (Key Observations)
- `Markdowns/3. bachelor_thesis_daniel_elis_compressed.md` (prior-work statistics); `content/04-design.tex` L457
- `figures/results/cs_ipc_progression_planner.png`, `cs_forest_cliffs_delta.png` (viewed)
- `bibliography.bib`; IAAS Scientific Writing Guidelines
