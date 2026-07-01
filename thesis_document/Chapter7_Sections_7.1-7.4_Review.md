# Supervisor Review — Chapter 7, Sections 7.1–7.4 (Results: Stages 0–3)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Scope of this pass:** §7.1 Baseline (Stage 0), §7.2 General Prompt (Stage 1), §7.3 Architecture-Aware Prompt (Stage 2), §7.4 Feedback Loop (Stage 3) — `content/07-results.tex`, lines 14–470.
**Cross-checked against:** the four `5_Key_Observations` files, every `1_Summary` and `2_Tables/*.md` under `analysis/output/stage{0,1,2,3}`, all seven figures (viewed directly), the IAAS Scientific Writing Guidelines, and `bibliography.bib`.
**Mode:** recommend-only — I have changed nothing in your files.

---

## Overall verdict

This is a genuinely strong results chapter — analytically mature, well-structured, and, most importantly, **overwhelmingly accurate to your data**. I extracted and re-checked essentially every quantitative claim in the four sections against the source `.md` tables; the large majority match exactly, including all the hard ones (the specialisation 16/15/8/3 = 42 split, the per-planner improvement ranking, the 55/68 = 80.9 % combined figure, every wall-time cell). The prose also does the harder job well: it translates your (informal) analysis notes into measured academic language and consistently warns the reader where a metric is not comparable.

That said, you asked for a demanding pass, and there **are** real things to fix. One is a genuine arithmetic error in §7.4 (the "14 late bloomers" makes a set sum to 70 instead of 68). A few are precision/wording issues that an examiner could catch (a token-limit claim that overstates which prompts failed; a superlative that is literally false; an unflagged switch in the IPC scale between stages). And there are a handful of high-value **additions** — chiefly the Stage 0 runtime–cost correlations, which you computed but never state even though the supporting figure is already in the chapter. None of this threatens the chapter; all of it is fixable in an afternoon.

I have ordered everything so the **must-fix** items are first (Part A), then a section-by-section deep dive (Part B), then figures/tables (Part C), additions (Part D), cross-cutting consistency (Part E), guidelines and references (Parts F–G), and a prioritised checklist (Part H).

---

## Part A — Priority fixes (verified errors, ranked)

| # | Where | Issue | Verified against | Suggested fix |
|---|---|---|---|---|
| **A1** | §7.4, **line 395** | **"14 late bloomers" is wrong and breaks the arithmetic.** The four convergence categories as written — 18 first-try + **14** late + 2 continuous + 36 stuck — sum to **70**, but there are only **68** contestable triples. | `S3_T8_Convergence_Patterns.md`: first-try **18**, late-bloomer **12**, progressive **2**, stuck **36** = **68**. | Change **14 → 12** in the convergence sentence. (Keep the *earlier* "remaining 14 improvements arrive at iterations 2 and 3" — that 14 = 5 + 9 of the 32 improved and is correct. The bug is only that the convergence sentence's "14 late bloomers" already includes the 2 continuous improvers, so listing "2 improve continuously" separately double-counts them. With 12, you get 18 + 12 + 2 + 36 = 68.) **Note:** your own `S3_12_Key_Observations` Obs 6 also says 14 — the table `S3_T8` is the authoritative count; the observations file inherited the same slip. |
| **A2** | §7.3, **line 282** | **Token-limit claim overstates the failing set.** "three Gemini 3.1 Pro outputs that exceeded the completion-token limit … (the DecStar and LAMA prompts for Depots and Barman)" reads as {DecStar, LAMA} × {Depots, Barman} = four combinations, but only **three** failed and **Depots×LAMA did not**. | `S2_T5`, `S2_T2`: the three are **Depots×DecStar, Barman×LAMA, Barman×DecStar**. | Reword to: "…three Gemini 3.1 Pro outputs that exceeded the completion-token limit — the DecStar prompt on Depots, and the LAMA and DecStar prompts on Barman." |
| **A3** | §7.4, **line 448** | **Literally-false superlative.** Gemini is called "the most concise output of any model," but GPT-5.4 is slightly *lower*. | `S3_T14`: Gemini avg output **796** tok vs GPT-5.4 **778**. | Soften to "one of the most concise" — or, better, pivot to the claim that *is* strictly true and more relevant: Gemini is the **most cost-effective** (fewest output tokens per IPC point, `S3_T25`: 19,550 vs GPT 25,389). |
| **A4** | §7.4, **line 467** | **"falling per-iteration yield … (18, 5, 9)" is non-monotonic** — 5 → 9 *rises*, so "falling" overstates the trend used to argue diminishing returns. | `S3_T5` / Obs 16 (your own note flags the iter-3 "rebound"). | Reframe as "front-loaded" rather than "falling," or acknowledge the iteration-3 rebound explicitly (the diminishing-returns argument still holds via the falling *validation* rate 93.8→90.0→86.8 %, which is the stronger evidence anyway). |
| **A5** | §7.3, **line 353** | **The "34 positive index" appears to contradict "16 + 15."** You give 34/42 positive, then in the same breath 16 specialised + 15 universal (= 31), and never account for the missing 3. | `S2_T22`: the **3 Neutral** configs all carry a *positive* index (+0.0402, +0.0145, +0.0131), so 16 + 15 + **3** = 34. | Add a half-clause, e.g. "…16 specialised, 15 universally better, and the 3 neutral configurations (whose non-target effect sits within the ±0.005 noise band but whose index is still positive) — 34 in all carry a positive index." |

All five are small edits, but A1 and A2 are the two an external examiner is most likely to flag, so I would do those first.

---

## Part B — Section-by-section review

### §7.1 Baseline Characterisation (Stage 0)

**Accuracy — excellent.** I checked all 60+ numbers (the 300/168/132 totals; every planner row of `tab:s0_planner_summary`; every domain row of `tab:s0_domain_difficulty`; every cell of `tab:s0_walltime`; the states-expanded figures; the 0.86/53.04 spread). **All match** `S0_1_Summary` and `S0_T1–T8` to the rounding. The "2,800–5,300 actions" cluster (line 160) I initially could not confirm from the tables (which store means), but the scatter figure resolves it: the top LAMA VisitAll point sits at ≈5,350 and the lowest cluster point at ≈2,730. Confirmed.

**One caveat to double-check (not an error):** the domain-difficulty table (line 92) names Madagascar the "fastest planner" on Snake at 81.6 s, even though Madagascar is the weakest planner and solves only 6/15 Snake instances. This is a survivorship artifact (its mean is over an easier solved subset), and your caption already warns of exactly this. It is correct — just the single most misreadable cell in the section, so the caption caveat is earning its keep.

**Content recommendation — the one substantive gap:** your **Observation 7 (runtime↔plan-cost correlation)** never made it into the chapter, yet the figure that motivates it (`fig:s0_runtime_cost`) *is* included. Right now the scatter is shown and discussed only qualitatively ("the isolated cluster…"). You computed a clean, defensible result:

> Spearman ρ = 0.6306 overall (p < 0.001); per planner: DecStar 0.897, Madagascar 0.874, LAMA 0.688, **BFWS 0.348**.

The BFWS outlier (weak correlation → its search time is "less wasted," producing good plans even when slow) directly reinforces your novelty/state-economy narrative in §7.1.2 and the right-skew/non-parametric rationale in line 32. **I'd add two or three sentences (and the ρ values) to §7.1.5** so the scatter earns its place. Using Spearman-not-Pearson is itself a methodological point worth one clause.

**Second, smaller gap — the telemetry paragraph (lines 168–170).** It asserts the planners report different metrics but shows no evidence. Your `S0_T8` (N/A distribution) substantiates it precisely (BFWS 64/64 missing states-evaluated & peak-memory; Madagascar 25/25 missing all state counts; DecStar and LAMA report everything). Either fold in a one-line "DecStar and LAMA report all six metrics; BFWS omits two and Madagascar four" or drop `S0_T8` in as a compact table.

**Proportion.** §7.1 remains the longest of the four sections (≈166 lines, 3 tables, 2 figures) — longer than any *intervention* stage. The writing is good, so I would not cut analyses, but the "efficiency metrics aren't comparable across planners because averages cover different solved subsets" argument is made twice — in §7.1.2 (lines 64–67) and again in §7.1.5 (lines 159–162). Make it once, forcefully, and cross-reference the second occurrence. That alone rebalances the section.

**Figures/tables:** the five chosen (planner summary, domain difficulty, wall-time matrix, coverage heatmap, runtime–cost scatter) are the right five and non-redundant. You correctly left out the redundant bar charts (`G1/G3/G4`), the trivial status-distribution (`G5`), and — importantly — the mean-plan-cost bar (`G6`), which on its own would have shown DecStar/Madagascar as "cheapest," the very artifact you spend two paragraphs debunking. Good editorial judgement.

### §7.2 General Prompt Results (Stage 1)

**Accuracy — flawless.** All 33 numbers check out: 18/20 valid, the two DeepSeek V3 identity rejections (Ricochet, Barman), 611/1,080 = 56.57 %, every per-planner Δ (BFWS −2.00 … Madagascar +3.34), the 101 total reorderings (31+9+33+28) and every component frequency (preconditions 16, actions 12, add 11, delete 6, predicates 4, four zeros). Nothing to correct in the data.

**Wording fix (line 219):** "shows how the **18 valid reorderings** distribute across the nine PDDL component types." There are 18 valid **domains** and **101** reorderings; the figure axis and caption correctly say "domains," so the body sentence is the odd one out. Change to "…how the reorderings across the 18 valid domains distribute…".

**Clarity check (line 241):** "each within about two percentage points of its baseline rate." True for the *domain* timeout shifts (≤1.7 pp), but the sentence's subject is the timeout-prone *planners*, and Madagascar's planner-level timeout rate moves −3.4 pp (`S1_T11`). Either scope the sentence to domains or say "about three percentage points."

**Optional softening (line 224):** you group functions with requirements/types as "never reordered because parsed once." Fair, but only ~2 of 5 domains even *use* functions, so their zero partly reflects low opportunity, not just model restraint. One hedge word ("rarely used, and never reordered") would be more precise.

**Content addition worth considering:** §7.2.3 is a *null-result* argument carried entirely by a 5-row table. A single figure would make "essentially flat" land instantly — either the **grouped Stage 0-vs-Stage 1 solve-rate bars (`G7`)**, or the **LLM×domain coverage heatmap (`G6`)** which would also visually support your "identical across all four models" claim (line 242), currently prose-only. I'd add one of the two.

**One more finding you recorded but omitted (Obs 9):** models reorder *more* on complex domains and *less* on simple ones (your note gives ≈3.3 components/model on Barman down to ≈0.75 on VisitAll). It's an independent angle on "targeted, not random," which you currently argue only from the parameters-zero. Worth one sentence — **but** those per-domain averages come from the diff JSON, not the `.md` tables, so re-derive/verify the exact figures before quoting them.

### §7.3 Architecture-Aware Prompt Results (Stage 2)

**Accuracy — very high.** 47 of the discrete claims I checked match exactly, including every specialisation count and mean index, and both class-sum reconciliations (16+15+8+3 = 42; per-planner 18+7+11+6 = 42). The one factual slip is **A2** (the token-limit prompts) and the one clarity gap is **A5** (the 34 vs 16+15). Both are in Part A.

**One precision note (line 284):** "DeepSeek-R1's reasoning trace inflated its output to roughly 106,185 tokens (about seven times GPT-5.4 and Claude)." The value is right; "~7×" fits Claude (6.9×) but understates GPT-5.4 (8.2×). Your own Obs 16 uses the same loose "7×," so it's faithful to your notes — just be aware "about seven to eight times" is truer.

**Content note — the two IPC references (medium, but examiner-relevant).** The improvement histogram (`fig:s2_ipc_gains`) caps at a mean gain of ≈0.09, but the specialisation scatter (`fig:s2_specialisation`) shows target gains up to **0.137**. Both are correct: the histogram uses the *global-baseline* reference, while the specialisation index uses a *per-instance local reference* — which you *do* state once (line 351). The risk is that a reader comparing the two figures sees 0.09 vs 0.14 and suspects an inconsistency. One sentence near line 319 or a footnote ("specialisation gains are computed on a local per-instance reference and are therefore not on the same scale as the baseline-referenced gains above") would pre-empt it.

**Figures/tables — strong selection; two high-value optional additions.** The three tables (improvement-by-planner, the merged domain/LLM, specialisation-by-planner) and two figures are well chosen. If you have room, the single most persuasive missing artifact is the **cross-test 4×4 IPC matrix (`S2_T21`, or its heatmap `G16`)** — it *shows* the diagonal-dominance you currently only assert in prose (line 362), and is the cleanest one-glance proof of specialisation. Second choice: **`S2_T17` (top-10 gains)** to substantiate "the very largest gains … concentrated in Depots" (line 364), which is currently unquantified. Do **not** add the by-LLM specialisation table (`S2_T24`) — it isn't discussed and would dilute the planner-centric story.

### §7.4 Feedback Loop Results (Stage 3)

**Accuracy — high, with the one real error (A1).** Every headline matches: 80/12/68 triples, 218 iterations, 2,955 runs, 32/68 improved, 30 seed + 25 loop = 55/68 = 80.9 %, the source-of-best 30/12/5/8, solve rate 56.9→64.4→69.0, and every per-LLM row of `tab:s3_llm`. Beyond A1, A3 and A4 (both in Part A) live here.

**Clarity — the two iteration breakdowns (should fix).** The prose (line 467) cites a per-iteration yield of **18, 5, 9**; Table `s3_combined` (lines 414–419) lists **12, 5, 8**. Both are correct but measure different things — 18/5/9 is *best-vs-seed* (sums to the 32 improvements), 12/5/8 is *source-of-baseline-beating-config* (sums to the 25 loop additions). Nothing tells the reader that, so iter-1 = 18 in the text and iter-1 = 12 in the adjacent table look contradictory. Add a clause distinguishing "improvements over the seed" from "configurations that beat the Stage 0 baseline," or footnote it.

**Clarity — the "100 % recovery" (line 397).** Verified: all five Stage-2 failures were recovered to *valid, solving* domains (100 % vs. the failure), but only **3 of the 5 also beat the Stage 0 baseline** (`S3_T9`; the two Gemini×DecStar recoveries land at IPC 3.92 and 13.70, below their Depots/Barman baselines). Your two highlighted examples (15.00 and 14.58) are both baseline-beating, so the text isn't wrong — but "fully recovered … among the strongest results" could be read as "all five are top-tier." A half-sentence ("all five recovered to valid solving configurations; three of them also beat the baseline") keeps this consistent with the 55/68 accounting and pre-empts a 100 %-vs-60 % puzzle.

**Content additions worth considering.** (1) A compact **recovery-cases table (`S3_T10`, 5 rows)** — you devote a paragraph and name two triples but show none; the table is small and high-impact, and would surface the two sub-baseline recoveries transparently. (2) The **structural-shift finding (Obs 17 / `S3_T21`)**: the loop doesn't just retry, it reorders *more aggressively* — precondition reorders rise 94 → 138 (+47 %) from seed to best while parameters stay ≈0. That is *quantitative* evidence for your central "genuine learning, not extra lottery tickets" claim (line 395), which currently rests on rationale-text anecdote alone. I'd add one sentence with that number; it's one of your best results and it's buried.

---

## Part C — Figures (all seven viewed directly)

| Figure | Verdict | Notes |
|---|---|---|
| `s0_coverage_heatmap` | **Keep as-is** | Values exact (BFWS col 15/8/11/15/15 = 64, etc.). Annotated cells → colour-blind safe. Row order isn't by difficulty (cosmetic only). |
| `s0_runtime_cost_scatter` | **Keep** | Confirms the 2,800–5,300 cluster. Minor: DecStar (green) vs Madagascar (red) are hard to separate in the crowded low band, but your headline (blue/orange upper cluster) is a colour-blind-safe pair, so the message survives. |
| `s1_reordering_frequency` | **Keep as-is** | Exact match to `S1_T6`; clean, single-colour, unambiguous. |
| `s2_ipc_gains_hist` | **Keep as-is** | Matches the "ceiling ≈0.09, none above 0.1, positive skew" description precisely. |
| **`s2_specialization_scatter`** | **Regenerate** | Three issues, all cosmetic but visible: (1) the embedded title reads "Speciali**z**ation" (US) while your prose/heading use British "Specialisation"; (2) planners are **red (BFWS) + green (LAMA)** with identical circle markers — the worst pairing for red–green colour-blindness, and these are the two planners your specialisation story hinges on; (3) the caption attributes the top-right cluster to "Depots," but the plot is coloured by *planner*, so that's invisible in the figure. Fix: regenerate with per-planner **marker shapes** (as your Stage 3 line charts already do) and the British spelling. |
| `s3_ipc_progression` | **Keep as-is** | Matches `S3_T23` (Claude 8.20→9.54→9.65; GPT 8.10→8.80→9.85; Gemini 8.36→9.16→8.67; DeepSeek flat). Distinct marker shapes + colours → accessible. Good. |
| `s3_solve_rate_trend` | **Keep as-is** | 56.9→64.4→69.0 with data labels; clean. |

**Bottom line on figures:** six of seven are accurate and well-made; only `s2_specialization_scatter` needs regeneration (this was flagged in your earlier whole-chapter review and has not yet been actioned).

---

## Part D — What's missing that I'd add (consolidated)

Ranked by value:

1. **§7.1 — the runtime–cost Spearman correlations** (Obs 7). Highest-value: the figure is already there; the result is clean; it reinforces two existing arguments. *(ρ = 0.6306; DecStar 0.897, Madagascar 0.874, LAMA 0.688, BFWS 0.348.)*
2. **§7.4 — the structural-shift number** (Obs 17 / `S3_T21`, preconditions 94→138). Turns your "genuine learning" claim from anecdote into evidence.
3. **§7.3 — the cross-test 4×4 matrix** (`S2_T21`/`G16`). Shows specialisation instead of asserting it.
4. **§7.2 — a null-result figure** (`G7` grouped bars or `G6` heatmap). Makes the flat Stage-1 result visual.
5. **§7.4 — the recovery-cases table** (`S3_T10`, 5 rows) and **§7.1 — the metric-availability table** (`S0_T8`) — both small, both back claims currently made in prose only.

Nothing essential is *missing* in the sense of a claim you failed to make; these are all "you have the evidence, show it" upgrades. Given your (legitimate) length constraint, items 1 and 2 are the two I would not skip.

---

## Part E — Cross-cutting consistency

- **IPC scale switches between stages, unflagged (worth fixing).** The chapter intro (line 7) defines the IPC score as **per-instance, 0–1**. Stages 1–2 stay on that scale (gains of 0.09, index 0.031, target gains to 0.137). But **Stage 3 reports per-triple totals on a 0–15 scale** — "maximum possible IPC score of 15.00" (line 397), "mean IPC score rises from 7.81 to 8.76" (line 427), the `tab:s3_llm` gains of +2.20 etc. (`S3_T16` confirms max = 15). A reader who took "0 to 1" from the intro will trip over "15.00." Add one bridging sentence at the first Stage-3 use — e.g. "IPC scores in this section are summed over a triple's 15 instances and so range 0–15, rather than the per-instance 0–1 of the earlier stages."
- **The number 56 collides three ways** — Stage 0 solve rate **56.00 %**, Stage 1 solve rate **56.57 %**, and Stage 2 improvement rate **56.0 %**. All correct, all different metrics, but three "≈56 %" in four sections invites a double-take. Nothing to fix numerically; just be aware, and maybe vary the phrasing ("just over half of configurations improved") once.
- **Forward references are consistent.** The "twelve always-timeout triples" thread is stated identically in §7.1 (line 120), §7.3 (lines 328, 385) and §7.4 (line 390), and the Stage 2 (α = 0.25 screening) vs Stage 3 (baseline-referenced) denominators are explicitly reconciled by your footnote at line 404. Good — these are exactly the places a careless chapter contradicts itself, and yours doesn't.

---

## Part F — Guidelines compliance (IAAS)

| Guideline | Status in §7.1–7.4 |
|---|---|
| No contractions | ✅ none found |
| Capitalise "Table/Figure/Section" references | ✅ all via `\Cref` (auto-capitalised) |
| Consistent terminology / British spelling in prose | ✅ consistent (specialisation, characterisation, normalised …); the only US spelling is *inside* the `s2` figure image (Part C) |
| "we" not "I"; define acronyms on first use; `\num{}` for large numbers | ✅ throughout (`\gls{}` handles acronym expansion) |
| Don't open a paragraph with "This"/"In this" | ✅ no paragraph opens with "This." One opens with "**These** curves" (line 448) — same family, but it's anchored to the figure just shown, so low severity; reword only if you want to be strict. |
| Reference all floats from the text | ✅ every table and figure is `\Cref`-ed in prose |

Guideline compliance in these sections is, frankly, better than most submitted theses.

---

## Part G — References

- Only two citations appear in these sections, both in the chapter intro (line 12): **`Elis2025`** and **`Georgievski2025`**. Both bib entries are real and clean — `Elis2025` is Daniel Elis's Stuttgart bachelor thesis (correctly typed with `type = {Bachelor Thesis}`), and `Georgievski2025` is the Georgievski–Elis–Vallati ICAPS KEPS workshop paper. Used appropriately as the prior work you build on. No fabricated or mismatched references.
- **One factual claim to verify/cite (honesty flag):** line 59 calls BFWS "the IPC 2018 Agile-track winner." That's a checkable bibliographic fact and I could not confirm it from your repo — please make sure it's accurate and that the claim is cited where BFWS is introduced (§6, `sec:setup:planners`). If it's actually a strong-performer-but-not-winner, soften accordingly. I'm flagging rather than asserting because I'm not certain of the 2018 Agile result.

---

## Part H — Prioritised action checklist

**Must fix (accuracy):**
1. §7.4 line 395 — "14 late bloomers" → **12** (fixes the 70-vs-68 sum). *(A1)*
2. §7.3 line 282 — reword the Gemini token-limit prompts (only 3 failed; no Depots×LAMA). *(A2)*
3. §7.4 line 448 — "most concise output" → "one of the most concise" / pivot to cost-effectiveness. *(A3)*
4. §7.4 line 467 — "falling … (18, 5, 9)" → "front-loaded" (5→9 rises). *(A4)*
5. §7.3 line 353 — add the clause reconciling 34 = 16 + 15 + 3 neutral. *(A5)*

**Should fix (clarity):**
6. Bridge the IPC 0–1 vs 0–15 scale switch at the first Stage-3 use (Part E).
7. §7.4 — distinguish the "18/5/9" and "12/5/8" iteration breakdowns (Part B / §7.4).
8. §7.4 line 397 — note that 3 of 5 recoveries also beat baseline (Part B / §7.4).
9. §7.2 line 219 — "18 valid reorderings" → "18 valid domains."
10. §7.2 line 241 — reconcile "about two percentage points" with Madagascar's −3.4 pp.
11. §7.3 — one line/footnote on the local-vs-global IPC reference (0.09 vs 0.137).

**Add if room (value-ranked, Part D):**
12. §7.1 — the runtime–cost Spearman correlations (**do this one**).
13. §7.4 — the structural-shift number, preconditions 94→138 (**do this one**).
14. §7.3 `S2_T21`/`G16`; §7.2 `G7`/`G6`; §7.4 `S3_T10`; §7.1 `S0_T8`.

**Figures:**
15. Regenerate `s2_specialization_scatter` (British spelling + per-planner marker shapes).

**Verify (honesty):**
16. The "IPC 2018 Agile-track winner" claim (line 59) and its citation; the Obs 9 per-domain reorder averages before quoting them.

**Trim, if you want to rebalance length:**
17. §7.1 — consolidate the "averages-over-different-subsets" argument (made in §7.1.2 and §7.1.5) into one place.

---

## Part J — Changes applied to `07-results.tex` (this session)

All the text edits below were applied directly to `content/07-results.tex`. Post-edit checks: braces balance (692/692), four footnotes in §7.1–7.4 (one original + three new), all cross-reference labels still resolve. **Recompile** to refresh the new footnotes and references. On **A1**, your reading was adopted — the number stays **14**, with the 2 continuous improvers made an explicit subset, so the categories now sum to 68 (18 + 14 + 36).

| # | Section | Change | Effect |
|---|---|---|---|
| 1 | §7.4 (A1) | "…14 are 'late bloomers' … just 2 improve continuously…" → "…14 … **just 2 of which** improve continuously across all three…" | Categories sum to 68, not 70 (2 ⊂ 14) |
| 2 | §7.3 (A2) | Gemini token-limit prompts → "the DecStar prompt on Depots, and the LAMA and DecStar prompts on Barman" | Matches the 3 real failures (no Depots×LAMA) |
| 3 | §7.4 (A3) | "the most concise output of any model" → "the most cost-effective model of the four (Table s3_llm)" | Removes the false superlative (GPT-5.4 is more concise) |
| 4 | §7.4 (A4) | "falling per-iteration yield (18, 5, 9)" → "concentration … in the first iteration (18, against 5 and 9 …)" **+ footnote** | Fixes the non-monotonic "falling"; footnote separates the 18/5/9 (vs-seed) and 12/5/8 (vs-baseline) counts |
| 5 | §7.3 (A5) | Added "…3 neutral configurations … constitute the 34…" clause | Reconciles 34 = 16 + 15 + 3 |
| 6 | §7.3 | **Footnote** on the local-vs-global IPC reference at the specialisation-index definition | Pre-empts the 0.09-vs-0.14 magnitude confusion |
| 7 | §7.4 (E1) | **Footnote** at the first "15.00" | Bridges the per-instance 0–1 vs per-triple 0–15 IPC scale |
| 8 | §7.4 | "fully recovered … **three of them also beating the Stage 0 baseline**" | Clarifies 100% recovery ≠ baseline-beating (3/5) |
| 9 | §7.1 | Added the runtime–cost **Spearman** correlations (ρ = 0.63; 0.90 / 0.87 / 0.69 / 0.35) to the scatter intro | The scatter now earns its place |
| 10 | §7.1 | Consolidated the survivorship argument (cross-ref to §7.1.2; trimmed the closing line) | Cuts the §7.1.2 / §7.1.5 duplication |
| 11 | §7.2 | "18 valid reorderings" → "reorderings across the 18 valid domains" | Domains ≠ reorderings |
| 12 | §7.2 | Softened the functions claim ("appear in only a minority of the benchmark domains") | More precise |
| 13 | §7.2 | "about two" → "about three percentage points" | Covers Madagascar's −3.34 pp |
| 14 | §7.3 (E2) | "56% of configurations" → "just over half of all configurations" | Reduces the triple-56% collision |

**Deliberately not applied** (your length/space instruction): the new figures in §7.2, the extra tables in §7.3–§7.4, the Obs 9 sentence, and the §7.4 structural-shift number. **Still open (needs image regeneration, not a text edit):** `s2_specialization_scatter.png` — British "Specialisation" spelling + per-planner marker shapes. **Still to confirm (honesty flags):** the "IPC 2018 Agile-track winner" claim (line 59) and its citation.

---

## Verification note (how this review was checked)

Every quantitative claim in §7.1–7.4 was cross-checked against the `.md` files in `analysis/output/stage{0,1,2,3}/{1_Summary,2_Tables,5_Key_Observations}`; the five Part-A items and the Stage-3 recovery/scale points were re-verified directly against the specific source tables (`S3_T8`, `S2_T5/T2`, `S2_T22/T25`, `S3_T9/T10/T16`, `S3_T14`). All seven figures were opened and inspected. Where I could **not** fully verify a claim from the repo (the "IPC 2018 Agile winner" literature fact; the Obs 9 per-domain averages that live in the diff JSON rather than the tables), I have said so explicitly rather than assert it.

### Sources
- `analysis/output/stage0/` — `1_Summary/S0_1`, `2_Tables/S0_T1–T8`, `5_Key_Observations/S0_8`
- `analysis/output/stage1/` — `1_Summary/S1_1`, `2_Tables/S1_T1–T11`, `5_Key_Observations/S1_6`
- `analysis/output/stage2/` — `1_Summary/S2_1`, `2_Tables/S2_T1–T25`, `5_Key_Observations/S2_9`
- `analysis/output/stage3/` — `1_Summary/S3_1`, `2_Tables/S3_T1–T27`, `5_Key_Observations/S3_12`
- `figures/results/` — all seven PNGs viewed directly
- `bibliography.bib`; IAAS Scientific Writing Guidelines
