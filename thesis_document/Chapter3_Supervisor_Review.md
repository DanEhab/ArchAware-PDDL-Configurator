# Supervisor-Style Review — Chapter 3 (Related Work)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 3 (`content/03-related-work.tex`), cross-checked against the bibliography, the modified Georgievski paper, and Chapters 1–2.
**Date:** 26 June 2026
**Note:** You did not flag prior supervisor comments on this chapter, so this is a first-time review.

> **Read order.** Part A is the headline: a reference audit that found **four more references with fabricated/incorrect author names** (now fixed) — and a clear pattern that warrants a full-bibliography audit (see Part F). Part B checks content accuracy (the predecessor numbers, the comparison table). Part C is the IAAS related-work guideline check. Part D is cross-chapter consistency. Part E is the changelog. Part F is your action items.

---

## Overall assessment

Chapter 3 is **excellent in structure and argument** — arguably the strongest-written chapter so far. It does exactly what the IAAS "State of the Art" guideline asks: it defines four research areas, describes each work's contribution, explains how works build on or differ from one another, identifies limitations, and culminates in a clear three-gap statement with a comparison table that positions your thesis. The narrative flow from "classical configuration → LLM configuration → LLMs as modellers → LLMs as planners → gap" is logical and persuasive.

The content I could cross-check is **accurate**: the predecessor-study numbers all reconcile (see Part B), and the comparison table fairly characterises each work.

**However**, the reference audit is the headline. Continuing the pattern your supervisor first flagged in Chapter 1, I found **four more references in this chapter with wrong author names** — all classic generative-AI errors, all now fixed:

| Severity | Reference | Problem | Status |
|---|---|---|---|
| 🔴 High | `Bercher2025` | author "**Sunandha Sreetharan**" → real author is **Sarath Sreedharan** (a well-known planning researcher; the correct spelling already appears in two other entries in your `.bib`) | **Fixed** |
| 🔴 High | `Pallagani2024` | "**Keerthiram Roy**" → **Kaushik Roy**; "**Keerthana Murugesan**" → **Keerthiram Murugesan** (two names cross-contaminated) | **Fixed** |
| 🔴 High | `Tuisov2025` | "**Artem Tuisov**" → **Alexander Tuisov**; "**Yonathan Vernik**" → **Yonatan Vernik** | **Fixed** |
| 🟠 Medium | `Tantakoun2025` | "**Matthew Tantakoun**" → **Marcus Tantakoun** | **Fixed** |
| 🟡 Low | `Chrpa2020` | the commented-out block was still in the `.bib` (you intended to delete it) | **Removed** |
| 🟡 Low | Table caption said "planner-aware"; column header says "Arch.-Aware" | inconsistent terminology | **Fixed** ("architecture-aware") |
| 🟡 Low | Chapter opened with "This chapter surveys…" (guideline: don't open with *This*) | **Fixed** (reworded) |

> **This is now a systemic issue, not isolated.** Across Chapters 1–3 I have found wrong author names in **six** references: `Huang2025`, `Casciani2025`, `Bercher2025`, `Pallagani2024`, `Tuisov2025`, `Tantakoun2025`. Every one is an AI-generated `.bib` entry where the *paper* is real but the *author names* were hallucinated. **I strongly recommend a full author-by-author audit of the entire bibliography before submission** — see Part F. I'm happy to do this as a dedicated pass.

**Verdict:** The chapter's writing is ready. The bibliography needs the full audit. One content decision is yours (the `Tuisov2025` title — Part B4).

---

## Part A — Reference verification (Chapter 3)

Chapter 3 cites **26** references. I had already verified most in the Chapter 1–2 reviews; this round I verified the **7 new** ones and re-checked author names across the chapter against primary sources (ACL Anthology, IJCAI/ICAPS proceedings, arXiv, authors' own pages).

| Key | Used for | Verified against | Result |
|---|---|---|---|
| `Alarnaouti2023` | Reformulation survey (L50) | *Knowledge Engineering Review* 38:e9, 2023 | ✅ |
| `Helmert2009` | Predicate grouping (L77) | *Artificial Intelligence* 173(5–6):503–535 | ✅ |
| `Tantakoun2025` | Formaliser survey (L153) | ACL Findings 2025, pp. 25167–25188 | 🔧 author **Matthew → Marcus** |
| `Bercher2025` | Model repair survey (L162) | IJCAI 2025 | 🔧 author **Sunandha Sreetharan → Sarath Sreedharan** |
| `Pallagani2024` | LLM roles in APS (L201) | ICAPS 2024, pp. 432–444 | 🔧 authors **Kaushik Roy / Keerthiram Murugesan** |
| `Stein2025` | LLM action choice (L206) | ICAPS 2025 | ✅ |
| `Tuisov2025` | LLM heuristics (L207) | arXiv:2501.18784 | 🔧 authors **Alexander Tuisov / Yonatan Vernik**; title note (B4) |

(The 19 previously-verified references — `HoweDahlman2002`, `RiddleHolteBarley2011`, `Vallati2015`, `Vallati2021`, `McCluskey2017`, `Elis2025`, `Georgievski2025`, `FoxLong2003`, `Wei2022`, `HoweyLongFox2004`, `Guan2023`, `Oswald2024`, `Smirnov2024`, `Casciani2025`, `Huang2025`, `Vallati2025`, `Georgievski2026`, `Valmeekam2023`, `Kambhampati2024` — remain correct as fixed in earlier rounds.)

**On `Bercher2025` (optional):** the entry has no page numbers. The IJCAI 2025 proceedings list it (paper 1152). Consider adding pages for completeness, but verify them against the official proceedings (I did not want to insert a page range I couldn't fully confirm).

---

## Part B — Content accuracy

**B1 — Predecessor-study figures (§3.2): ✅ all reconcile.** I checked every quantitative claim about `Georgievski2025`/`Elis2025`:
- "700 total configurations (7 LLMs × 4 temperatures × 5 prompts × 5 domains)" → 7·4·5·5 = **700** ✓
- "514 (73%) pass syntactic validation and 350 (50%) preserve semantic equivalence, yielding 343 fully valid" → matches the Elis thesis exactly (514 = 73.43%, 350 = 50.00%, 343 valid) ✓
- "34,300 planner execution results" → 343 configs × 5 planners × 20 instances = **34,300** ✓
- The seven LLMs (incl. **Claude 3.5 Sonnet**) and five domains (Barman, Genome Edit Distances, Thoughtful, Transport, Visit All) and temperatures (0.0/0.2/0.5/0.7) match the *modified* paper. ✓ (Good catch on your part using "Claude 3.5 Sonnet" — an internal comparison doc in your repo says "Claude 3.7", but the published paper says 3.5 Sonnet, which you matched.)

*Two figures I could not independently verify* (they come from the paper's results section, which I don't have in full): the **pseudo-R² of 0.22** (L99) and the per-model validity rates **96% / 14% / 22%** (L100). They are internally plausible and consistent with the Elis thesis summary, but please double-check them against the paper/your own data before submission — I don't want to vouch for figures I couldn't see at the source.

**B2 — Comparison table (Table 3.1): ✅ accurate.** I checked each row against the cited work: task classification, architecture-aware = ✗ for all prior work, the feedback column (with the footnote `a` correctly distinguishing *implicit* planner-evaluation feedback in Vallati from LLM feedback), and the one-line limitations are all fair. Selecting only the "key approaches" (and omitting surveys/foundational works) is acceptable for a positioning table. The "This thesis" row is correctly the only one with both ✓.

**B3 — `Guan2023` description (L139): minor.** You write that Guan's loop feeds "plan execution failures" back to the LLM. Guan et al.'s corrective signals come primarily from **PDDL validators and human-in-the-loop feedback** (plus environment interaction), not specifically "plan execution failures." Consider softening to "validation and environment feedback." Minor; not changed.

**B4 — `Tuisov2025` — your decision (title + description).**
- *Title:* the arXiv paper (2501.18784) was **retitled** in its latest version. v1 (Jan 2025, which you cite) was "LLM-Generated Heuristics for AI Planning: Do We Even Need Domain-Independence Anymore?"; the current v4 (Jan 2026) is "Successor-Generator Planning with LLM-generated Heuristics." Decide which to cite — if you cite the latest version, update the title in the `.bib`. I left your (original) title in place and only fixed the authors.
- *Description (L207):* you call them "domain-specific heuristic functions"; the paper generates **problem-/instance-specific** heuristics from successor generators. Consider "instance-specific." Minor.

**B5 — Planner naming (L91): verify.** You list the predecessor's width-based planners as "SIW and BFS$_f$." An internal comparison doc in your repo refers to "SIW-BFSF." Please confirm the exact planner name(s) against Table 1 of `Georgievski2025`. Likely fine, but worth a glance.

---

## Part C — IAAS related-work guideline check

| Guideline (State of the Art section) | Status | Notes |
|---|---|---|
| Identify & describe key research areas | ✅ | Four clearly delineated areas, ordered by relevance. |
| Summarise state of the art per area; major works | ✅ | Each area surveys the major works. |
| For each work: what it is + contribution | ✅ | Done consistently. |
| How it builds on / differs from prior work | ✅ | Explicit (e.g., Riddle "extends" Howe; configuration as "specialised reformulation"). |
| Discuss limitations / remaining gaps | ✅ | Per-area limitation paragraphs + the dedicated §3.5. |
| Position your own research | ✅ | §3.5 maps each of three gaps to a stage of your pipeline, plus the comparison table. |
| Don't open paragraph/section with "This" | 🔧 | Chapter opened with "This chapter surveys…" — **reworded**. No other offenders. |
| Capitalised cross-references | ✅ | `\Cref` throughout. |
| Acronyms, British spelling, "we", present tense | ✅ | Consistent; LTeX tag `en-GB`. |
| Tables referenced from text & captioned | ✅ | Table 3.1 is introduced (L217) and captioned; caption now matches the column header (Part E). |
| Numeric citations not used as sentence subjects | ✅ | Uses `\citeauthor{}~\cite{}` form correctly throughout. |

This chapter is the best example so far of the IAAS related-work structure. No substantive guideline issues remain.

---

## Part D — Cross-chapter consistency

- **Three properties / three gaps:** §3.2 (L71) and §3.5 restate the three validity properties and three research gaps consistently with Chapters 1–2 and the modified paper. ✓
- **"Three-stage validation pipeline of Georgievski2025 → four-level"** (L240): consistent with Ch. 1 (Contribution 3) and Ch. 4. The modified paper's Algorithm 1 confirms the predecessor pipeline is three stages, so the "extends to four-level" claim is accurate. ✓
- **Architecture-aware terminology:** now consistent (the table caption fix aligns "architecture-aware" with the `Arch.-Aware` column and the rest of the thesis). ✓
- **`Cassano2023`:** your fix from the Chapter 1 round is in place and correctly cited in both Ch. 1 (L49) and Ch. 2 (L232); the entry ("Can It Edit?…", arXiv:2312.12450) is correct. ✓
- **Bibliography sync:** resolved — `Cassano2023` is present; the stray commented `Chrpa2020` block has now been removed.

---

## Part E — Changelog (edits applied)

**`bibliography.bib`**
1. `Tantakoun2025` author: "Matthew Tantakoun" → "Marcus Tantakoun".
2. `Bercher2025` author: "Sunandha Sreetharan" → "Sarath Sreedharan".
3. `Tuisov2025` authors: "Artem Tuisov and Yonathan Vernik" → "Alexander Tuisov and Yonatan Vernik".
4. `Pallagani2024` authors: "Keerthiram Roy" → "Kaushik Roy"; "Keerthana Murugesan" → "Keerthiram Murugesan".
5. `Chrpa2020`: removed the leftover commented-out block (uncited; you had intended to delete it).

**`content/03-related-work.tex`**
6. Chapter opening: "This chapter surveys the research most closely related to the present thesis." → "The present chapter surveys the research most closely related to this work." (guideline: no "This"-opening).
7. Table 3.1 caption: "whether the approach is planner-aware" → "…architecture-aware" (match the column header and thesis terminology).

**Deliberately not changed:** `Tuisov2025` title (B4 — your decision); `Guan2023`/`Tuisov2025` descriptions (B3/B4 — minor wording).

---

## Part F — Action items for you

> ### 🔴 1. Run a full author-by-author audit of the bibliography (highest priority)
> Six references across Chapters 1–3 had hallucinated author names (`Huang2025`, `Casciani2025`, `Bercher2025`, `Pallagani2024`, `Tuisov2025`, `Tantakoun2025`). The papers are real; the names were invented or mangled. This is exactly what your supervisor warned about, and an examiner who spot-checks references will notice. **Every entry's author list should be checked against the primary source (ACL Anthology / dblp / publisher page) before submission.** I can do this as one dedicated pass over all ~48 entries and report a table of corrections — just say the word.

2. **`Tuisov2025` title (B4):** decide whether to cite the original or the retitled latest version, and update the `.bib` accordingly.
3. **Verify the two predecessor figures** I couldn't see at source (pseudo-R² 0.22; 96%/14%/22% validity rates) against the paper/your data (B1).
4. **Confirm the predecessor planner name** "BFS$_f$" vs "SIW-BFSF" against the paper's Table 1 (B5).
5. **Optional:** add page numbers to `Bercher2025`; soften the `Guan2023` "plan execution failures" wording (B3).
6. **Recompile** and confirm the bibliography renders with the corrected names (I can't run `biber`/`minted` here; all edits are non-structural).

---

## Sources used for verification

- *LLMs as Planning Formalizers: A Survey* (Tantakoun, Muise, Zhu), ACL Findings 2025 — authoritative author list: https://aclanthology.org/2025.findings-acl.1291/
- *A Survey on Model Repair in AI Planning* (Bercher, **Sreedharan**, Vallati), IJCAI 2025: https://www.ijcai.org/proceedings/2025/1152 · author copy: https://bercher.net/publications/2025/Bercher2025ModelRepairSurvey.pdf
- *Successor-Generator Planning with LLM-generated Heuristics* (**Alexander Tuisov, Yonatan Vernik**, Alexander Shleyfman), arXiv:2501.18784: https://arxiv.org/abs/2501.18784
- *On the Prospects of Incorporating LLMs in APS* (Pallagani, Muppasani, **Kaushik Roy**, Fabiano, Loreggia, **Keerthiram Murugesan**, …), ICAPS 2024: https://ojs.aaai.org/index.php/ICAPS/article/view/31503 · https://arxiv.org/abs/2401.02500
- *Automating the Generation of Prompts for LLM-based Action Choice in PDDL Planning* (Stein, Fišer, Hoffmann, Koller), ICAPS 2025: https://ojs.aaai.org/index.php/ICAPS/article/view/36126
- *Reformulation Techniques for Automated Planning: A Systematic Review* (Alarnaouti, Baryannis, Vallati), KER 38:e9, 2023: https://www.cambridge.org/core/journals/knowledge-engineering-review/article/reformulation-techniques-for-automated-planning-a-systematic-review/E212DBCBDA3179FC41BFAD86A8E4332F
- *Concise Finite-Domain Representations for PDDL Planning Tasks* (Helmert), AIJ 173, 2009: https://www.sciencedirect.com/science/article/pii/S0004370208001926
- *Can It Edit? Evaluating the Ability of LLMs to Edit Code* (Cassano et al.), arXiv:2312.12450: https://arxiv.org/abs/2312.12450

*Local source:* `VIP Documents/3. Literature Review/Dr Ilche's Paper modified.pdf` (used to reconcile the §3.2 predecessor figures and the three-stage pipeline claim).
