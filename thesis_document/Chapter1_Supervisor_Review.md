# Supervisor-Style Review — Chapter 1 (Introduction)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 1 (`content/01-introduction.tex`), with cross-checks against the abstract and Chapters 2–6
**Date:** 26 June 2026

> **How to read this document.** Part A verifies that the 14 comments from your supervisor were correctly fixed. Part B is a reference-by-reference verification of every citation in Chapter 1 (this is where the most important findings are). Part C lists new issues I found. Part D is the IAAS-guideline check. Part E is the exact changelog of edits I already applied to your `.tex`/`.bib` files. Part F is the short list of things only *you* should action. Sources I verified against are at the end.

---

## Overall assessment

Chapter 1 is in **strong shape**. The narrative is well-structured, the research questions and contributions are crisp, and — importantly — **all 14 of your supervisor's comments have been addressed substantively**, not just cosmetically. The chronological reframing (Howe → Riddle → Vallati), the broadened three-gap structure, the explicit SQ1 coverage in the methodology, and the addition of `Georgievski2026`/`Vallati2025` are all done correctly.

However, the single most important issue your supervisor raised — *"The references appear random; if you use Gen AI tools for this, please be very careful"* — was still live. While re-verifying every reference against primary sources, I found **four reference errors of exactly that type**, including **two fabricated/incorrect author names** that are classic generative-AI hallucinations:

| Severity | Reference | Problem | Status |
|---|---|---|---|
| 🔴 High | `Huang2025` | Authors were **"Can Huang and Lihao Zhang"** — the real authors are **"Cassie Huang and Li Zhang"** | **Fixed** |
| 🔴 High | `Casciani2025` | Authors were **"Alessandro Casciani … Clara Weinhuber"** — the real authors are **"Angelo Casciani … Christoph Weinhuber"** | **Fixed** |
| 🟠 Medium | `Vallati2021` | DOI `…09587-x` does not resolve to this paper; correct DOI is `10.1007/s10817-021-09592-1` | **Fixed** |
| 🟡 Low | `Vallati2015` | Missing page numbers (guideline requires full citation info) — added `1704–1711` | **Fixed** |
| 🟡 Low | `Chrpa2020` | Unused **and** malformed (a habilitation thesis typed as `@Unpublished`; your supervisor's Comment 2) | **Commented out** |

I also found **two places where later text reintroduced wording your supervisor had you remove from Chapter 1** (the abstract and Chapters 4–5). These are fixed for consistency. After all fixes, Chapter 1 and its references are sound. A few items in Part F still need *your* judgement.

**Verdict:** Ready to move on, once you action Part F (most importantly: re-compile with `biber` in your own environment to confirm the bibliography renders, and add one code-specific citation).

---

## Part A — Verification of the 14 supervisor comments

All line references are to the **current** `01-introduction.tex`.

| # | Supervisor's comment | Required change | Status | Where / how |
|---|---|---|---|---|
| 1 | `[Geo23]` is not a standard reference for the "initial state → goal state" claim; use *Automated Planning: Theory and Practice* and/or an intro AI-planning text | Replace with standard textbook(s) | ✅ Done | L15 now cites `GhallabNauTraverso2004` + `RussellNorvig2021`. The first is exactly the book he recommended. |
| 2 | `[Chr20…]` is a poor reference here, **and** the entry is incorrect (it is a habilitation thesis, published as such) | Remove from this claim; fix entry | ✅ Done (Ch.1) / ⚠️ see Part F | Removed from Ch.1 (L13). The malformed entry is now commented out in the `.bib` (it was no longer cited anywhere). |
| 3 | `[GVSK23]` (= `Guan2023`) is not a good reference for that statement | Remove from that position | ✅ Done | Removed from the opening; `Guan2023` now appears (correctly) at L51 among LLM PDDL-generation works. |
| 4 | "planning engine (the search algorithm)" — modular separation goes beyond search | Drop "(the search algorithm)" | ✅ Done | L19 now reads "between the planning engine and the domain model (the formal description of the environment's dynamics)". **Note:** the same narrowing had crept back into the *abstract* — see C1. |
| 5 | Discuss works chronologically; start with Howe, not Vallati | Reorder | ✅ Done | L28–29 and L42–44 now go Howe (2002) → Riddle (2011) → Vallati (2015/2021). |
| 6 | Howe/Riddle cannot "corroborate" Vallati — they predate it | Remove "corroborate" framing | ✅ Done | Now "Building on these observations, Vallati … provided the first systematic evidence". "Corroborate" appears nowhere in the body. |
| 7 | `[HD02]` and `[RHB11]` are also related works | Include them in the SOTA/related discussion | ✅ Done | L42–43 integrate both into the state-of-the-art narrative (and Ch.3 §3.1 opens with them). |
| 8 | Add `Georgievski2026` alongside `Vallati2025` | Add citation | ✅ Done | L51 cites `{Vallati2025, Georgievski2026}`. The `.bib` entry matches the BibTeX he supplied exactly. |
| 9 | Gaps focus only on LLM approaches; what about pre-LLM (Vallati et al.)? | Broaden the gaps | ✅ Done | Now **three** gaps; Gap 1 is "Dependence on costly evaluations in classical approaches" (`Vallati2015/2021`). |
| 10 | LLM-Modulo idea is not only Kambhampati — also `Vallati2025` | Add citation | ✅ Done | L74 cites both `Kambhampati2024` and `Vallati2025`. |
| 11 | Also ask whether planners are *resilient* to configuration due to their architecture | Add this nuance | ✅ Done | L79–80 add the resilience question; carried through to SQ5 and Contribution 4. |
| 12 | Which part of the methodology covers SQ1? | Make SQ1 coverage explicit | ✅ Done | L121–123 add the preliminary architectural-analysis phase, explicitly tagged **(SQ1)**. |
| 13 | (a) "official" VAL? (b) add a reference for VAL | Soften "official"; cite VAL | ✅ Done (Ch.1) | L145: "official" removed; `HoweyLongFox2004` added. **Note:** "official validator of the IPC" still appeared in Ch.4 and Ch.5 — see C2. |
| 14 | The findings *are* the contributions (re. "Cross-architecture empirical analysis") | Reframe contributions around findings | ✅ Done | Contribution 4 is now "Cross-architecture empirical findings"; Contributions 1–3 also foreground empirical evidence. |

**Conclusion for Part A: 14/14 addressed correctly.**

---

## Part B — Reference verification (every citation in Chapter 1)

I verified all **21** distinct references cited in Chapter 1 against primary sources (publisher pages, ACL Anthology, IJCAI/AAAI/NeurIPS proceedings, arXiv, and the authors' own publication lists). Legend: ✅ correct · 🔧 fixed · ⚠️ optional improvement.

| Key | Used for (Ch.1) | Verified against | Result |
|---|---|---|---|
| `GhallabNauTraverso2004` | Definition of AI planning (L15–16) | Morgan Kaufmann, 2004, ISBN 978-1-55860-856-6 | ✅ Correct (this is the book your supervisor recommended) |
| `RussellNorvig2021` | Definition of AI planning (L15) | AIMA 4th ed., Pearson | ✅ Correct (US ed. is sometimes dated 2020 — trivial, see C-minor) |
| `McDermott1998` | PDDL (L20–21) | Yale CVC TR-98-003, 1998; all 8 authors match | ✅ Correct |
| `HoweDahlman2002` | Structural sensitivity (L28, L43) | JAIR, vol. 17, pp. 1–33, 2002 | ✅ Correct |
| `RiddleHolteBarley2011` | Representation affects rankings (L28, L43) | SARA 2011; Riddle, Holte, Barley | ✅ Correct |
| `Vallati2015` | First systematic configuration (L29, L44, L62) | IJCAI 2015 | 🔧 **Added missing pages 1704–1711** |
| `Vallati2021` | Extended configuration study (L29, L45, L62) | *J. Automated Reasoning* 65(6):727–773, 2021 | 🔧 **DOI corrected** to `10.1007/s10817-021-09592-1` |
| `McCluskey2017` | Manual configuration is expensive (L31) | K-CAP 2017; McCluskey, Vaquero, Vallati | ✅ Correct (venue name slightly informal — see C-minor) |
| `Zhao2023` | LLM survey (L49) | arXiv:2303.18223 | ✅ Correct |
| `Minaee2024` | LLM survey (L49) | arXiv:2402.06196 | ✅ Correct |
| `Oswald2024` | LLMs generate PDDL domains (L51) | ICAPS 2024, pp. 423–431; all 6 authors match | ✅ Correct |
| `Guan2023` | LLMs build world models (L51) | NeurIPS 2023; Guan, Valmeekam, Sreedharan, Kambhampati | ✅ Correct |
| `Smirnov2024` | Generating PDDL domains (L51) | arXiv:2404.07751; all 4 authors match | ✅ Correct (title-case "Consistent" — see C-minor) |
| `Casciani2025` | LLM PDDL generation (L51) | Author's own publication list + DiAG/Sapienza copy | 🔧 **Authors corrected** → Angelo Casciani … Christoph Weinhuber |
| `Huang2025` | LLMs as planning formalizers (L51) | ACL Anthology 2025.acl-long.242 | 🔧 **Authors corrected** → Cassie Huang and Li Zhang |
| `Vallati2025` | KE in the LLM era (L51, L74) | ICAPS 2025, vol. 35, pp. 391–395 | ✅ Correct |
| `Georgievski2026` | LLMs need external validators (L51) | Matches supervisor-supplied BibTeX | ✅ Correct |
| `Elis2025` | Predecessor thesis (L53) | Title verified against the thesis PDF in your repo | ✅ Correct |
| `Georgievski2025` | Associated study (L53, L162) | Title verified against `2. Dr. Ilche's paper.md` | ✅ Correct |
| `Kambhampati2024` | LLM-Modulo (L74, L159) | ICML 2024 (PMLR v235) | ✅ Correct |
| `HoweyLongFox2004` | VAL tool (L145) | ICTAI 2004 (16th IEEE ICTAI) | ✅ Correct |

### The four reference errors, in detail

**B1 — `Huang2025`: fabricated author names (🔴 High).**
The bibliography listed *"Can Huang and Lihao Zhang"*. The authoritative ACL Anthology record (and the paper PDF) give the authors as **Cassie Huang and Li Zhang**. Title, venue (ACL 2025, Vol. 1: Long Papers), and pages (4880–4904) were all correct — only the names were wrong, which is the signature of an LLM-hallucinated citation. *Independent cross-check:* your supervisor's own paper (`Georgievski2025`) cites this work as "Huang and Zhang 2025", confirming the corrected names.

**B2 — `Casciani2025`: two wrong author first-names (🔴 High).**
The bibliography listed *"Alessandro Casciani … Clara Weinhuber"*. The correct authors (verified on the first author's own academic publication list) are **Angelo Casciani, Giuseppe De Giacomo, Andrea Marrella, Christoph Weinhuber**. Two given names were wrong ("Alessandro"→"Angelo", "Clara"→"Christoph").

**B3 — `Vallati2021`: wrong DOI (🟠 Medium).**
The DOI `10.1007/s10817-021-09587-x` did not resolve to this article in any source I checked. The correct DOI for *"On the Importance of Domain Model Configuration for Automated Planning Engines"* (J. Automated Reasoning 65(6):727–773) is **`10.1007/s10817-021-09592-1`** (Springer article URL). I am highly confident in this correction; please click-confirm it once on Springer when convenient (see Part F).

**B4 — `Vallati2015`: missing page numbers (🟡 Low).**
Your supervisor's guidelines require full citation information (pages included). I added **pp. 1704–1711** (IJCAI 2015 proceedings).

**B5 — `Chrpa2020`: unused + malformed (🟡 Low).**
This entry is **not cited anywhere** in the thesis (only inside a `% comment`), and it was typed as `@Unpublished` although, as your supervisor noted, it is a **habilitation thesis**. I commented the entry out (so it can't render incorrectly) and left an inline note explaining how to re-add it properly if you ever cite it. I could not independently verify the exact publication details of this habilitation, so I deliberately did **not** invent them.

---

## Part C — New issues found (and what I did about them)

### Consistency with the supervisor's comments (the ones you asked me to guard against)

**C1 — Abstract reintroduced "search algorithms" (Comment 4 echo). → Fixed.**
The abstract said *"yet the internal **search algorithms** of different planners process these models in fundamentally different ways."* This is exactly the narrowing your supervisor corrected in Comment 4 — and it slightly undercuts your own thesis, whose whole premise is that planners differ across their **entire architecture** (parser, grounder, search, heuristics), not just search. Changed to *"the internal **architectures** of different planners…"*.

**C2 — "official validator of the IPC" reappeared in Ch.4 and Ch.5 (Comment 13 echo). → Fixed.**
Although you removed "official" before VAL in Chapter 1, the phrase *"the official validator of the \gls{ipc}"* survived in `04-design.tex` (§V2) and `05-implementation.tex` (§VAL integration). I softened both to *"the standard plan validator used in the IPC"*. (VAL was *developed for* IPC-3 and is the de-facto standard, but "official" is the unverifiable wording your supervisor flagged.) The separate phrases "official VAL **repository**" / "official Fast Downward **repository**" in Ch.5 are fine and were left as-is — those legitimately refer to the canonical GitHub repos.

### Citation–claim matching (the supervisor's core concern — worth your attention)

**C3 — Code-refactoring claim is supported only by general LLM surveys (recommend; not auto-fixed).**
L49 states that LLMs have shown *"remarkable capabilities in generating, editing, and refactoring code-like artefacts from natural-language instructions"* — but cites only two **general** LLM surveys (`Zhao2023`, `Minaee2024`), which don't specifically establish code-editing ability. Interestingly, your supervisor's paper supports the same sentence with a code-specific reference (*Cassano et al. 2023*). **Recommendation:** add one code-specific citation here. I did **not** auto-insert one because doing so without verifying the exact entry is precisely the failure mode we're trying to avoid. Candidates to verify yourself: *Cassano et al. (2023)* "Can It Edit? Evaluating the Ability of LLMs to Edit Code" (the one your supervisor used), or Chen et al. (2021) "Evaluating Large Language Models Trained on Code." See Part F.

**C4 — Foundational textbook cited for very modern applications (minor).**
L16 cites `GhallabNauTraverso2004` (a 2004 book) for applications *"ranging from robotics and logistics to cloud orchestration and intelligent buildings."* A 2004 textbook cannot support "cloud orchestration." Either present those as illustrative examples (no citation implying the book covers them) or add an application-specific reference (e.g., your group's smart-buildings planning work). Low priority, but it's the same category of issue your supervisor is sensitive to.

### Factual claims about the predecessor work — checked, all accurate

I verified the quantitative claims in §1.2 against the source paper and the Elis thesis:
- *"seven LLMs, five planners, and five benchmark domains"* (L54) — ✅ matches `Georgievski2025` ("seven LLMs, five prompting strategies, five planners, and five domains") and the Elis thesis.
- The *"three key results"* (L55) — ✅ each maps to a stated contribution of `Georgievski2025` (semantic-equivalence feasibility; LLM choice dominates; planner-dependent gains).
- *"four architecturally diverse planners (BFWS, LAMA, DecStar, Madagascar), five IPC domains, four LLMs"* (L149) — ✅ consistent with the rest of the thesis.

**C5 — "three-stage pipeline of Georgievski2025" (verify wording).**
Contribution 3 (L162) says you extend *"the three-stage pipeline of `Georgievski2025`"* with an extraction stage. This is **internally consistent** with Ch.4 (§4.x: "This four-level pipeline extends the three-stage validation approach … by adding the V1 extraction stage"), and plausible (V2 syntactic / V3 identity / V4 semantic). Just double-check that the predecessor paper itself describes its pipeline as three stages, since that paper's text emphasises "a validation pipeline" without an explicit count — you want the attribution to be exact.

**C6 — SQ1 is a long compound sentence (style).** Minor: SQ1 (L99) packs three questions into one sentence. Consider splitting for readability (your guidelines favour short sentences).

---

## Part D — IAAS scientific-writing guideline check (Chapter 1)

| Guideline | Status | Notes |
|---|---|---|
| Use **we**, not I | ✅ | Consistent throughout. |
| Active voice / present tense | ✅ | Predominantly active, present tense. |
| Don't open a paragraph/section with "This"/"In this" | ✅ | No paragraph opens with "This"/"In this" (checked all 17 paragraph openings). |
| Capitalise cross-references ("Chapter", "Section") | ✅ | Uses `\Cref{}`, which auto-capitalises. |
| Define acronyms at first use; don't over-use | ✅ | Handled by the `\gls{}`/glossary system (AI, PDDL, LLM, SAT, BFWS, LAMA, IPC). |
| No contractions | ✅ | None in body text. (The "Can't" inside the `Kambhampati2024` title is the real paper title — correct to keep.) |
| Consistent terminology | ✅ | "planning engine", "domain model", "configuration" used consistently. |
| Consistent spelling | 🔧 | Prose is **British** (optimise, behaviour, licence) and `babel` is set to `main=english` — but every file declared `% LTeX: language=en-US`. I switched the six LTeX tags to **en-GB** so the spell-checker matches your actual (and department-preferred) style. *Output is unaffected — this is an editor directive only.* |
| References as sentence subjects only as "Author (year)" | ✅ | You consistently use `\citeauthor{}~\cite{}` ("Howe and Dahlman [HD02]") — the correct pattern for alpha-style keys. |
| Full citation info; consistent fields | ✅ (after fixes) | Page numbers now present where expected; see B4. |
| Links state access date | ✅ | Footnote URLs use "(accessed June 2026)". |
| Figures/Tables connected by reference | n/a | Chapter 1 contains **no figures or tables** (correct for an introduction) — I confirmed there are none to check. |

---

## Part E — Changelog (edits already applied to your files)

**`bibliography.bib`**
1. `Huang2025` author: `Can Huang and Lihao Zhang` → `Cassie Huang and Li Zhang`
2. `Casciani2025` author: `Alessandro Casciani … Clara Weinhuber` → `Angelo Casciani … Christoph Weinhuber`
3. `Vallati2021` DOI: `10.1007/s10817-021-09587-x` → `10.1007/s10817-021-09592-1`
4. `Vallati2015`: added `pages = {1704--1711}`
5. `Chrpa2020`: commented out (unused + malformed), with an inline note on how to re-add it correctly

**`main-english.tex`** (Abstract)
6. "internal **search algorithms** of different planners" → "internal **architectures** of different planners"

**`content/04-design.tex`**
7. §V2: "VAL tool …, the **official validator** of the IPC." → "…, the **standard plan validator used in** the IPC."

**`content/05-implementation.tex`**
8. §VAL integration: "VAL tool …, the **official validator** of the IPC, containerised…" → "…, the **standard plan validator used in** the IPC, containerised…"

**LTeX language tag → `en-GB`** in: `01-introduction.tex`, `02-background.tex`, `03-related-work.tex`, `04-design.tex`, `05-implementation.tex`, `main-english.tex`

**Deliberately *not* changed:** the two `optimizing` spellings in `04-design.tex` (lines 394 & 562) are **inside verbatim prompt listings** — they reproduce the literal prompts sent to the LLMs, so they must stay American-spelled for reproducibility. (I checked; this is not a spelling inconsistency.)

*Verification:* after the edits, every one of the 46 `\cite` keys used across the thesis still resolves to a live `.bib` entry (the commented-out `Chrpa2020` was uncited, so nothing breaks). No structural LaTeX was altered.

---

## Part F — Action items for you (not auto-fixed)

1. **Re-compile with `biber` in your own environment (Overleaf/local) and check the bibliography.** I could not run a full build here (`biber`/`minted` aren't installed in this sandbox), and my edits were non-structural, so compilation isn't at risk — but you should still rebuild and confirm: (a) the corrected entries render, (b) no "undefined reference" warnings, (c) the bibliography list looks consistent.
2. **Add one code-specific citation at L49** (C3). Verify the exact entry before adding — suggested: *Cassano et al. 2023* (the one `Georgievski2025` uses) or *Chen et al. 2021*.
3. **Decide on `Chrpa2020`** (B5): either delete it entirely, or re-add it as a properly-typed habilitation thesis with verified details (institution, etc.).
4. **Click-confirm the `Vallati2021` DOI** once on Springer (B3) — I'm confident, but a 10-second check closes it out.
5. **Optional:** consider whether the modern-applications citation at L16 (C4) should be adjusted.
6. **Optional housekeeping:** the `% Comment N:` tracking notes are helpful now but you may want to strip them before final submission (they don't appear in the PDF, so this is cosmetic).
7. **Academic-integrity step (important):** complete your faculty's AI-use declaration (*Persönliche Erklärung*) and follow the IAAS GenAI guidelines your supervisor linked. The reference errors found here are a concrete reminder of why every AI-assisted citation must be checked against the primary source.

---

## Sources used for verification

- ACL Anthology — *On the Limit of Language Models as Planning Formalizers* (Huang & Zhang, 2025): https://aclanthology.org/2025.acl-long.242/
- Angelo Casciani — publications list (authoritative author/Weinhuber names): https://angelo-casciani.github.io/publications/
- Springer — *On the Importance of Domain Model Configuration for Automated Planning Engines* (J. Automated Reasoning, 2021): https://link.springer.com/article/10.1007/s10817-021-09592-1
- IJCAI 2015 proceedings — *On the Effective Configuration of Planning Domain Models* (pp. 1704–1711): https://www.ijcai.org/Proceedings/15/Papers/243.pdf
- ICAPS/AAAI — *Knowledge Engineering for Planning and Scheduling in the LLM Era* (vol. 35, pp. 391–395): https://ojs.aaai.org/index.php/ICAPS/article/view/36142
- ICAPS/AAAI — *Large Language Models as Planning Domain Generators* (pp. 423–431): https://ojs.aaai.org/index.php/ICAPS/article/view/31502
- NeurIPS 2023 — *Leveraging Pre-trained LLMs to Construct and Utilize World Models* (Guan et al.): https://proceedings.neurips.cc/paper_files/paper/2023/hash/f9f54762cbb4fe4dbffdd4f792c31221-Abstract-Conference.html
- arXiv — *Generating consistent PDDL domains with LLMs* (Smirnov et al., 2024): https://arxiv.org/abs/2404.07751
- JAIR — *A Critical Assessment of Benchmark Comparison in Planning* (Howe & Dahlman, 2002): https://www.jair.org/index.php/jair/article/view/10305
- SARA 2011 — *Does Representation Matter in the Planning Competition?* (Riddle, Holte, Barley): https://webdocs.cs.ualberta.ca/~holte/Publications/SARA11.pdf
- PMLR v235 — *Position: LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks* (Kambhampati et al., 2024): https://proceedings.mlr.press/v235/kambhampati24a.html
- ACM K-CAP 2017 — *Engineering Knowledge for Automated Planning: Towards a Notion of Quality*: https://dl.acm.org/doi/10.1145/3148011.3148012
- Strathprints — *VAL: Automatic Plan Validation …* (Howey, Long, Fox, 2004): https://strathprints.strath.ac.uk/2550/
- arXiv — *A Survey of Large Language Models* (Zhao et al.): https://arxiv.org/abs/2303.18223
- arXiv — *Large Language Models: A Survey* (Minaee et al.): https://arxiv.org/abs/2402.06196
- Morgan Kaufmann / ACM — *Automated Planning: Theory & Practice* (Ghallab, Nau, Traverso, 2004): https://dl.acm.org/doi/book/10.5555/975615
- AIMA — *Artificial Intelligence: A Modern Approach*, 4th ed. (Russell & Norvig): https://aima.cs.berkeley.edu/

*Local sources verified in your repository:* `Markdowns/2. Dr. Ilche's paper.md` (title/abstract of `Georgievski2025`) and `Markdowns/3. bachelor_thesis_daniel_elis_compressed.md` (title of `Elis2025`).
