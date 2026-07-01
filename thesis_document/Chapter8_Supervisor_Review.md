# Supervisor Review — Chapter 8 (Threats to Validity)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration · Youssef · University of Stuttgart (IAAS)
**Scope:** the full chapter — `content/08-threats-to-validity.tex` (≈104 lines).
**Cross-checked against:** `cross_stage/12_Threats_Validity` (G-T44/45/46), Chapters 4–7, §6 domain quantification, `bibliography.bib`, IAAS guidelines.
**Mode:** changes applied directly, length-conscious.

---

## Verdict — rating 9 / 10

This is a genuinely good threats chapter, and shorter than you feared. It uses the standard four-type framework with a proper citation (`Wohlin2012`), covers all four validity classes — internal, external, construct, and statistical conclusion — and, crucially, pairs *every* threat with either a concrete mitigation already built into the design or an explicit residual-risk statement. That mitigation discipline is exactly what an examiner looks for and is the difference between a real threats chapter and a box-ticking one. It is also accurate: I cross-checked its factual claims against Chapters 4–7 and §6 and found no contradictions.

I made only two changes (below) — one guideline fix and one consolidation that makes the chapter shorter *and* better-organised. Nothing else needed correcting. After these, the chapter is essentially submission-ready; the residual gap to a 10 is simply that a threats chapter's ceiling is bounded by the study it describes, not by anything you did wrong here.

---

## Part A — Changes applied

| # | Where | Change | Why |
|---|---|---|---|
| **1** | Intro L4 | Reworded the chapter opener: **"This chapter examines the threats…" → "As with any empirical study, the findings reported in \Cref{ch:results} are subject to threats to validity, discussed here under the standard four-type classification…"** | IAAS guideline: do not open a chapter/section/paragraph with "This". Also adds a forward link to \Cref{ch:results}. |
| **2** | §8.1 / §8.2 | **Consolidated the "Single-run evaluation" threat (External) into "LLM non-determinism" (Internal)**; removed the standalone External paragraph. | It was *redundant* — its own text said "(as noted above)" — and *mis-categorised*: single-run reproducibility is a causal-integrity/conclusion issue, not a generalisability one. Its unique points (planners are deterministic, so generation is the sole stochastic component; full repetition was infeasible on a bachelor budget) are preserved inside the non-determinism paragraph. Net: one fewer paragraph, cleaner taxonomy, no lost content. |

Both edits verified on the real file. External validity now reads Domain → Planner → LLM-versions → (Construct), and the merged non-determinism paragraph is coherent. Braces balance (each edit was brace-balanced); recompile to refresh the new `\Cref{ch:results}` link. *(Note: your Linux/bash view of this one file is a stale snapshot — the real file is ~104 lines and correct; ignore any tool that reports it as 14–18 lines.)*

---

## Part B — What I verified (all correct)

- **Cross-references — 100% resolve.** All 16 `\Cref` targets exist: `sec:setup:{hyperparameters,hardware,domains,planners,llms,arch_aware_prompt}`, `sec:design:{stage3,stage2:improvement}`, `eq:ipc_score`, `sec:results:{stage0:cost,cross_stage:validation,statistical_validation(:stage/:factors/:selection)}`, `tab:stat_pairwise`, plus the new `ch:results`.
- **Citations valid.** `Wohlin2012` (@Book — the standard validity-framework reference) and `Romano2006` (Cliff's δ thresholds) both exist and are used correctly.
- **No contradictions with Chapters 6–7.** The architectural ranking (BFWS > LAMA > Madagascar > DecStar, §8.2) matches §7.5; the δ=0.30 "small but substantive" framing (§8.4) matches §7.6; the α=0.25 screening → α=0.05/0.0083 confirmatory story (§8.3–8.4) matches Chapters 4 and 7; the structural-metric ranges cited in §8.2 (|A|∈[1,12], |O_t|∈[0,7], max arity∈[2,6]) **match the §6 domain-quantification table exactly**; the Cliff's δ thresholds (0.147/0.33/0.474) match `Romano2006` and §7.6.
- **Consistent with §7.7's bridge.** §7.7 explicitly forwards "the limited planner and domain coverage" and the small-effect caveat to this chapter, and §8.2/§8.4 deliver exactly those — the two chapters interlock correctly.
- **Guidelines.** No contractions; British spelling consistent (generalisability, operationalisation); "we" not "I"; every threat is a named `\paragraph`; all references capitalised via `\Cref`. After change #1, no paragraph opens with "This/These/In this".

---

## Part C — Optional, non-blocking notes

1. **"All five significant pairwise results survive this correction" (§8.4, Multiple comparisons).** Consistent with the thesis's framing (five contrasts judged significant; S2-vs-S3 set aside via Nemenyi + effect size in §7.6). Strictly, S2-vs-S3's Wilcoxon p (2.3×10⁻³) also clears the Bonferroni threshold, so a very literal reader might expect "six". No change needed — it matches how §7.6 defines significance — but if you want to pre-empt the nitpick, "All five *strongly* significant results…" costs one word.
2. **Coverage is complete; do not add threats.** Your own analysis (G-T44/45/46) enumerates internal/external/construct only; you additionally (and rightly) include statistical conclusion validity. Everything material is covered — adding more would work against your shorter-is-better goal.

That's the chapter. It is concise, rigorous, honest about its limits, and correctly wired to the rest of the thesis.

### Sources
- `content/08-threats-to-validity.tex`; `content/06-experimental-setup.tex` (§6 quantification); Chapters 4, 7 (`ch:results`)
- `cross_stage/12_Threats_Validity/Section12_Threats_to_Validity_Report.md`
- `bibliography.bib` (`Wohlin2012`, `Romano2006`); IAAS Scientific Writing Guidelines
