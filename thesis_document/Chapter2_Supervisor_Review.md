# Supervisor-Style Review — Chapter 2 (Background)

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**Reviewer pass:** Chapter 2 (`content/02-background.tex`), cross-checked against Dr. Georgievski's *modified* paper, the abstract, and Chapters 1, 3, 4.
**Date:** 26 June 2026

> **Read order.** Part A verifies the 8 supervisor comments. Part B checks the formal definitions / Eq. (2.1) / the validity properties against the *modified* paper (Comments 6–8) — this is where the one subtle finding is. Part C is the reference verification. Part D covers the listings/figure (including the Blocksworld PDDL). Part E is guidelines, Part F cross-chapter consistency, Part G the changelog, Part H your action items. **Please read the ⚠️ callout in Part H about the bibliography file first.**

---

## Overall assessment

Chapter 2 is **strong and well-organised**. It follows the IAAS structure for a background chapter (focused, critical, logically layered from planning → PDDL → search paradigms → configuration → LLMs → LLM-Modulo), and **all 8 of your supervisor's comments are addressed**, including the non-trivial ones (definitions moved to running text with italicised concepts; `par(a)` added to the action-schema tuple, the configuration definition, and Eq. (2.1); the validity list expanded from two to three properties).

The formal content now matches the **modified** paper closely. I found **one subtle deviation** worth a sentence to your supervisor (the `par(a)` term in the structural-transformation condition — Part B3), **two reference errors** (one venue clearly wrong, one title of your supervisor's own paper), and **one minor style item** — all fixed or flagged below.

| Severity | Item | Status |
|---|---|---|
| 🟠 Medium | `GnadHoffmann2018` cited as **IJCAI 2018, pp. 4979–4986** — no such version exists; the real publication is **Artificial Intelligence 257 (2018), pp. 24–60** | **Fixed** (entry changed to `@Article`) |
| 🟠 Medium | `Georgievski2023` (your supervisor's own paper) titled "Software Development **Lifecycle**…" — the ICSOFT 2023 paper you cite is titled "Software Development **Life Cycle**…" | **Fixed** |
| 🟡 Low | One paragraph opened with "This separation…" (guideline: don't open with *This*) | **Fixed** (reworded) |
| 🔵 Confirm | Structural-transformation condition includes `par(a)`; the modified paper's Definition 1 lists only `{F, A, pre(a), eff(a)}` there | **Flagged** (your version is more consistent — see B3) |
| ⚠️ Important | The `bibliography.bib` I can access does **not** contain `Cassano2023` and still has the commented-out `Chrpa2020` — i.e. your Chapter 1 follow-up edits are not in this copy | **See Part H** |

**Verdict:** Chapter 2 is in good shape. The only thing needing your judgement is the one-line `par(a)` question (B3) and the bibliography-sync issue (Part H).

---

## Part A — Verification of the 8 supervisor comments

| # | Comment | Status | Where / how |
|---|---|---|---|
| 1 | `[GEV25]` should have `booktitle = {ICAPS Knowledge Engineering for Planning and Scheduling Workshop}` | ✅ Done | `Georgievski2025` now has exactly that booktitle; L23 cites it for the formalism. |
| 2 | Remove the `Definition 2.1`/`2.2` environments; put them in running text with concepts in italics | ✅ Done | L25–35 are now running text; `\emph{state}`, `\emph{action schema}`, etc. No `definition` environments remain (verified). |
| 3 | In the domain-file definition, remove `[GNT04;` | ✅ Done | L55 now cites only `McDermott1998`. |
| 4 | `[Geo23; MVV17]` — order chronologically | ✅ Done | L185 renders chronologically (McCluskey 2017 → Georgievski 2023). See note ▼ on the rendering. |
| 5 | "Definitions 2.1 and 2.2" → "the formalism of a planning problem" | ✅ Done | L191 now reads "Although the formalism of a planning problem treats … as unordered sets". |
| 6 | Adjust Def. 2.3 to include `par(a)` (per modified paper) | ✅ Done | `par(a)` added to the action-schema tuple (L27) and the configuration definition (L201). See B1. |
| 7 | Adjust Eq. (2.1) | ✅ Done | Eq. (2.1) now includes `|par(a)|!` and matches the modified paper exactly. See B2. |
| 8 | "two properties" → there are three | ✅ Done | L215–220 now list **three**: structural transformation, syntactic validity, semantic equivalence. See B3. |

**Note on Comment 4 (rendering).** Your fix uses two separate `\cite` commands (`\cite{McCluskey2017};~\cite{Georgievski2023}`), which renders as **"[MVV17]; [Geo23]"** — chronological, as the supervisor asked. I checked whether to merge them into one `\cite{...}`; I deliberately did **not**, because your bibliography uses `bibstyle=alphabetic` with `sortcites=true`, so a single grouped citation would be re-sorted by author name to "[Geo23; MVV17]" — reintroducing exactly the wrong order the supervisor flagged. Your two-citation form is the correct workaround. (Only cosmetic downside: two brackets instead of one. Acceptable.)

---

## Part B — Formal content vs the *modified* paper (Comments 6–8)

I compared L25–35, L199–220, and Eq. (2.1) line-by-line against *Dr Ilche's Paper modified.pdf* (Background + Definition 1).

**B1 — Definitions (L25–35, L199–203): ✅ match.**
The action schema is now `⟨par(a), pre(a), del(a), add(a)⟩` with `par(a)` a set of variables — exactly as in the modified paper (the original, unmodified paper had `⟨pre(a), del(a), add(a)⟩` without `par(a)`). State, applicability, successor state, domain model `⟨F, A⟩`, planning task, solution plan, and `Plans(D, P)` all match the modified paper verbatim. Moving these to running text with italicised terms (Comment 2) is done cleanly.

**B2 — Eq. (2.1): ✅ exact match.**
$$|\mathcal{C}(D)| = |F|!\cdot|A|!\cdot\prod_{a\in A}\big(|par(a)|!\cdot|pre(a)|!\cdot|eff(a)|!\big)$$
This is identical to the modified paper, including the new `|par(a)|!` factor (Comment 7). ✓

**B3 — The three validity properties (L215–220): ✅ match, with one subtle deviation to confirm.**
Properties 2 (syntactic validity) and 3 (semantic equivalence, `D⪯ ∈ C(D) ⇒ Plans(D,P)=Plans(D⪯,P)`) match the modified paper exactly. Property 1 (structural transformation) is where your text differs slightly from the source:

- **Your Chapter 2 (L217):** `∃ X ∈ {F, A, par(a), pre(a), eff(a)} : ⪯_{X,D⪯} ≠ ⪯_{X,D}`
- **Modified paper, Definition 1, condition 1:** `∃ X ∈ {F, A, pre(a), eff(a)} : …` — i.e. **without `par(a)`**.

So your version *adds* `par(a)` to the existential set. This is arguably **more correct than the source**: since `par(a)` is part of the configuration definition (L201) and appears in Eq. (2.1), a pure parameter reordering should also count as a structural transformation — otherwise the definition is internally inconsistent. The modified paper appears to have a minor internal inconsistency here (it includes `par(a)` in the configuration/cardinality but omits it from condition 1).

**My recommendation:** keep your version (with `par(a)`) for internal consistency, but add a half-sentence or mention it to your supervisor, since it deviates from the literal text of the paper he pointed you to. I did **not** auto-change this — it's a judgement call, and your version is the defensible one. (If he prefers a verbatim match, simply delete `par(a)` from the set on L217.)

*Bonus consistency check:* the modified paper's validation pipeline (Algorithm 1) is indeed **three stages** (parse/syntactic → normalise + identity → element-level semantic). This confirms the "three-stage pipeline of `Georgievski2025`" attribution used in Chapter 1 (Contribution 3) and Chapter 4 (§V-pipeline) — so that claim is accurate.

---

## Part C — Reference verification (Chapter 2)

Chapter 2 cites **28** distinct references. 13 were already verified in the Chapter 1 review; I verified the **15 new** ones against primary sources this round. ✅ correct · 🔧 fixed.

| Key | Used for | Verified against | Result |
|---|---|---|---|
| `FoxLong2003` | PDDL 2.1 (L49) | JAIR 20:61–124, 2003 | ✅ |
| `BonetGeffner2001` | Heuristic search (L146,148) | *Artificial Intelligence* 129(1–2):5–33 | ✅ |
| `HoffmannNebel2001` | Delete-relaxation/FF (L148) | JAIR 14:253–302, 2001 | ✅ |
| `RichterWestphal2010` | Landmark heuristics/LAMA (L150) | JAIR 39:127–177, 2010 | ✅ |
| `LipovetzkyGeffner2012` | Width-based search (L154,157) | ECAI 2012, pp. 540–545 | ✅ |
| `LipovetzkyGeffner2017` | BFWS (L158) | AAAI 2017, 31(1), pp. 3590–3596 | ✅ |
| `GnadHoffmann2018` | Decoupled search (L162,166) | **AIJ 257:24–60, 2018** (not IJCAI) | 🔧 **venue/type corrected** |
| `KautzSelman1992` | SAT planning (L169) | ECAI 1992, pp. 359–363 | ✅ |
| `Rintanen2012` | SAT heuristics (L170,173) | *Artificial Intelligence* 193:45–86 | ✅ |
| `Georgievski2023` | Modelling choices (L185) | ICSOFT 2023, pp. 751–760 | 🔧 **title corrected** ("Life Cycle") |
| `Brown2020` | Few-shot/GPT-3 (L231,243,264,274,276) | NeurIPS 2020, 33:1877–1901 | ✅ |
| `Vaswani2017` | Transformer (L237–240) | NeurIPS 2017 | ✅ (page range minor — see ▼) |
| `Valmeekam2023` | LLMs can't plan (L254,293) | NeurIPS 2022 FMDM Workshop / arXiv 2206.10498 | ✅ (year note — see ▼) |
| `Kojima2022` | Zero-shot CoT (L269,283) | NeurIPS 2022, 35:22199–22213 | ✅ |
| `Wei2022` | Chain-of-Thought (L280,282) | NeurIPS 2022, 35:24824–24837 | ✅ |

### The two reference errors, in detail

**C1 — `GnadHoffmann2018`: wrong venue/type (🟠).**
The entry was `@InProceedings`, *Proceedings of the 27th IJCAI*, pp. 4979–4986. Across three searches (dblp, the authors' own page, Semantic Scholar) the only publication of "Star-Topology Decoupled State-Space Search" is the **journal** version: *Artificial Intelligence*, vol. 257 (2018), pp. 24–60 (`dblp:journals/ai/GnadH18`). I could find **no** IJCAI 2018 version, and pp. 4979–4986 do not correspond to it. I changed the entry to `@Article` with the journal, volume, and pages. *Please sanity-check this once* — if you deliberately meant an IJCAI-18 journal-track presentation, verify it exists; otherwise the journal citation is the correct, primary one.

**C2 — `Georgievski2023`: wrong title (🟠, and it's your supervisor's own paper).**
The entry cited the ICSOFT 2023 paper (pp. 751–760) but titled it "Software Development **Lifecycle** for Engineering AI Planning Systems." The ICSOFT/SciTePress paper at those pages (DOI 10.5220/0012149100003538) is titled "Software Development **Life Cycle** for Engineering AI Planning Systems" (two words). The one-word "Lifecycle" belongs to a *different* companion paper ("Conceptualising Software Development Lifecycle…", IEEE). Corrected to "Life Cycle." Getting your examiner's own title exactly right is worth it.

### Minor reference notes (optional, not auto-changed)
- **`Vaswani2017` pages:** listed as 6000–6010; the NeurIPS 2017 proceedings are also widely cited as 5998–6008. Both appear in the wild; pick one and be consistent. Trivial.
- **`Valmeekam2023` year:** the `booktitle` says "NeurIPS **2022** … Workshop" but the `year` field is 2023. Consider setting `year = {2022}` to match the workshop (the original is arXiv 2206.10498, Dec 2022), unless you are intentionally citing a later version.

---

## Part D — Listings, figure, and the Blocksworld example

**Blocksworld PDDL (Listings 2.1 / 2.2): ✅ correct and consistent.**
I checked the PDDL by hand:
- The domain declares the 5 standard predicates (`on, ontable, clear, handempty, holding`) and the 4 standard actions (`pick-up, put-down, stack, unstack`) with correct preconditions/effects. ✓
- The problem `blocks-3-0` initial state is internally consistent: `b2` on the table with `b1` on it (so `b1` clear, `b2` not clear), `b3` on the table and clear, `handempty`. ✓
- The goal `(and (on b1 b2) (on b2 b3))` and the caption ("construct a tower b1–b2–b3", "b1 on b2 with b3 on the table") match the listing. ✓ The instance is solvable. Good, accurate illustrative example.

**Figure 2.1 (LLM-Modulo loop): ✅ fine.** Original TikZ diagram; caption correctly cites `Kambhampati2024`; the generate–test–critique narrative (L296–306) matches the figure. The `\dingcheck` glyph it uses **is** defined in `main-english.tex` (so it compiles).

**Compile safety: ✅.** Both `\dingcheck` (used in the figure) and the `lstdefinelanguage{PDDL}` (used by both listings) are defined in `main-english.tex`. No missing-command risk from this chapter.

---

## Part E — IAAS guideline check (Chapter 2)

| Guideline | Status | Notes |
|---|---|---|
| Use **we** | ✅ | "We denote / We survey / We equip / we adopt". |
| Active voice / present tense | ✅ | Consistent. |
| Don't open a paragraph/section with "This" | 🔧 | One instance (the "This separation…" paragraph after the problem-file list) — **reworded** to "The separation of the two files…". All section/subsection openings are clean. |
| Capitalised cross-references | ✅ | `\Cref` used throughout ("Chapter", "Section", "Figure"). |
| Define acronyms at first use | ✅ | `\gls` handles AI/PDDL/LLM/IPC/SAT/CoT; STRIPS and ADL are spelled out at first use (L48). |
| No contractions | ✅ | Body is clean. ("Let's think step by step" on L283 is a quoted trigger phrase — correct to keep.) |
| Consistent technical terminology | ✅ | "domain model", "planning engine", "configuration", "structural sensitivity" used consistently. |
| Consistent British spelling | ✅ | categorise/behaviour/optimisation/artefact/favourable — consistent; LTeX tag is `en-GB`. |
| Figures/tables/listings referenced from text | ✅ | Listings 2.1/2.2 and Figure 2.1 are all introduced by `\Cref` before they appear. |
| Math notation consistent | ✅ | `F, A, par(a), pre(a), eff(a), C(D), ⪯, Plans(·)` used consistently and match later chapters. |

---

## Part F — Cross-chapter consistency

- **Three-property validity framing** is now consistent everywhere: Ch. 2 (L215), Ch. 3 (L71, "structural transformation, syntactic validity, semantic equivalence"), and Ch. 4 (L744). No chapter still says "two properties." ✓
- **`par(a)` / Eq. (2.1) notation** appears only in Ch. 2; Chapters 3–4 refer back to `\Cref{sec:bg:configuration}` rather than restating the formula, so the B3 `par(a)` nuance lives in exactly one place (good — only one spot to adjust if your supervisor wants the verbatim-paper version).
- **"search algorithm" vs "architecture"**: Ch. 2's search-paradigm section correctly frames planners as differing across whole *algorithmic pipelines* (parser/grounding/heuristics/search), consistent with the Chapter 1 abstract fix from last round. ✓
- **`GnadHoffmann2018`** is also cited later (DecStar/decoupled search in Ch. 4–6); changing its entry type to `@Article` does not affect those citations — they still resolve to the same key. ✓

---

## Part G — Changelog (edits applied)

**`bibliography.bib`**
1. `GnadHoffmann2018`: `@InProceedings` / IJCAI 2018 / pp. 4979–4986 → `@Article` / *Artificial Intelligence* / vol. 257 / pp. 24–60.
2. `Georgievski2023`: title "Software Development **Lifecycle** …" → "Software Development **Life Cycle** …".

**`content/02-background.tex`**
3. L72: "**This separation** enables domain-independent planning:" → "**The separation of the two files** enables domain-independent planning:" (guideline: no "This"-opening).

**Deliberately not changed:** the Comment-4 citation (two-`\cite` form is the correct way to force chronological order under `sortcites=true`); the `par(a)` term in the structural-transformation condition (B3 — your version is more consistent; flagged for your decision).

---

## Part H — Action items for you

> ### ⚠️ 1. Bibliography sync — please check first
> The `bibliography.bib` in the folder I'm connected to **does not contain `Cassano2023`** and still has the **commented-out `Chrpa2020`** block from the Chapter 1 review. In other words, your stated Chapter 1 follow-ups ("added Cassano et al. 2023", "deleted Chrpa") are **not present in this copy**, and no content file cites `Cassano2023` here either (so this copy is self-consistent, just missing those changes).
>
> This strongly suggests you are editing a **different copy** (e.g. Overleaf) than the one synced to this session. Please confirm we are working on the same file before merging my edits — otherwise my Chapter 2 fixes (in this copy) and your Cassano/Chrpa edits (in your copy) will live in two places. If you tell me which copy is authoritative, I can re-apply everything there.

2. **`par(a)` in the structural-transformation condition (B3):** decide whether to keep it (recommended — internally consistent) or delete it to match the modified paper verbatim. Worth a one-line mention to your supervisor either way.
3. **Sanity-check `GnadHoffmann2018`** now reads as the AIJ 2018 journal article (C1).
4. **Optional:** `Valmeekam2023` year (2022 vs 2023) and `Vaswani2017` page range — trivial consistency tidy-ups.
5. **Recompile** in your environment and confirm the bibliography renders (I can't run `biber`/`minted` here; all my edits are non-structural).

---

## Sources used for verification

- *Star-topology decoupled state space search* (Gnad & Hoffmann), **AIJ 257:24–60, 2018** — dblp: https://dblp.org/rec/journals/ai/GnadH18.html · authors' copy: https://fai.cs.uni-saarland.de/hoffmann/papers/ai18.pdf
- *Software Development Life Cycle for Engineering AI Planning Systems* (Georgievski), ICSOFT 2023 — SciTePress: https://www.scitepress.org/Papers/2023/121491/121491.pdf
- *Planning as heuristic search* (Bonet & Geffner), AIJ 129, 2001: https://dl.acm.org/doi/10.1016/S0004-3702(01)00108-4
- *The FF Planning System* (Hoffmann & Nebel), JAIR 14, 2001: https://www.jair.org/index.php/jair/article/view/10276
- *The LAMA Planner* (Richter & Westphal), JAIR 39, 2010: https://dl.acm.org/doi/10.5555/1946417.1946420
- *Width and Serialization of Classical Planning Problems* (Lipovetzky & Geffner), ECAI 2012: https://ebooks.iospress.nl/volumearticle/7029
- *Best-First Width Search* (Lipovetzky & Geffner), AAAI 2017: https://ojs.aaai.org/index.php/AAAI/article/view/11027
- *Planning as Satisfiability* (Kautz & Selman), ECAI 1992 — dblp: https://dblp.org/rec/conf/ecai/KautzS92.html
- *Planning as satisfiability: Heuristics* (Rintanen), AIJ 193, 2012: https://www.sciencedirect.com/science/article/pii/S0004370212001014
- *PDDL2.1* (Fox & Long), JAIR 20, 2003: https://www.jair.org/index.php/jair/article/view/10352
- *Attention Is All You Need* (Vaswani et al.), NeurIPS 2017: https://papers.nips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html
- *Language Models are Few-Shot Learners* (Brown et al.), NeurIPS 2020: https://papers.nips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html
- *Chain-of-Thought Prompting* (Wei et al.), NeurIPS 2022: https://papers.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html
- *Large Language Models are Zero-Shot Reasoners* (Kojima et al.), NeurIPS 2022 — dblp: https://dblp.org/rec/conf/nips/KojimaGRMI22.html
- *LLMs Still Can't Plan* (Valmeekam et al.), arXiv 2206.10498 — dblp: https://dblp.org/rec/journals/corr/abs-2206-10498.html

*Local source verified:* `VIP Documents/3. Literature Review/Dr Ilche's Paper modified.pdf` (Background + Definition 1) — used to confirm Comments 6, 7, 8.
