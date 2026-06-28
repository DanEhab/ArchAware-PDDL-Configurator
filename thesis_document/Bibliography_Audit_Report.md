# Bibliography Audit Report — Full Author-by-Author Verification

**Thesis:** Architecture-Aware LLM-Based PDDL Domain Model Configuration
**Author:** Youssef · University of Stuttgart (IAAS)
**File audited:** `bibliography.bib` (47 reference entries)
**Date:** 26 June 2026
**Method:** Every entry checked against primary sources — ACL Anthology, dblp, IJCAI/ICAPS/AAAI/NeurIPS/PMLR proceedings, Springer/Cambridge/ScienceDirect, arXiv, and authors' own pages. Focus: author names and order, then title/venue/year.

---

## Headline

I verified all **47** entries. Combined with the chapter reviews, the audit found **14 entries with errors** — and the dominant problem is exactly what your supervisor warned about at the very start: **fabricated or mangled author names in the AI-generated entries.** In total, **8 entries had wrong author names**, plus 1 author-order error, plus title/venue/DOI/page problems.

Every error is now **fixed**. The papers were all real; the metadata was not. After this pass, I could not find a remaining incorrect author name in the bibliography (with one honest caveat about `Cassano2023`, noted below).

**Error tally (all rounds):**

| Category | Count | Entries |
|---|---|---|
| Wrong author name(s) | 8 | `Huang2025`, `Casciani2025`, `Bercher2025`, `Pallagani2024`, `Tuisov2025`, `Tantakoun2025`, `Zhao2023`, `Cassano2023` |
| Wrong author order | 1 | `Kambhampati2024` |
| Wrong title | 2 | `Georgievski2023`, `Cassano2023` |
| Wrong venue / entry type | 1 | `GnadHoffmann2018` |
| Wrong DOI | 1 | `Vallati2021` |
| Missing pages | 1 | `Vallati2015` |
| Malformed / removed | 1 | `Chrpa2020` |

---

## Fixes applied in this audit pass (new)

**1. `Cassano2023` — most serious (wrong authors *and* title).**
The entry you added carried the author list of a **different paper** — *MultiPL-E* (Gouwar, Nguyen, Nguyen, Phipps-Costin, Pinckney, Yee, Zi, Feldman, Greenberg, Jangda) — attached to the *Can It Edit?* arXiv ID (2312.12450), with a truncated title ("…to Edit Code"). Corrected to the real paper:
- **Title:** "Can It Edit? Evaluating the Ability of Large Language Models to **Follow Code Editing Instructions**"
- **Authors:** Federico Cassano, Luisa Li, Akul Sethi, Noah Shinn, Abby Brennan-Jones, Anton Lozhkov, Carolyn Jane Anderson, Arjun Guha.
- *Honest caveat:* I used the 8 authors listed for the arXiv preprint (2312.12450) on the arXiv/HuggingFace page. The later published version (COLM 2024) lists a few additional middle authors. Since you cite the arXiv preprint, the 8-author list is consistent — but if you switch to the published version, paste its full author list. This is the one entry where I'd suggest you double-check the author list against whichever version you intend to cite.

**2. `Zhao2023` — wrong author name.** "Xiaolian Wang" → **"Xiaolei Wang"** (5th listed author of *A Survey of Large Language Models*). The other nine listed names + "and others" are correct.

**3. `Kambhampati2024` — wrong author order.** The 4th/5th authors were swapped: "…Lin Guan and **Kaya Stechly and Mudit Verma** and…" → "…Lin Guan and **Mudit Verma and Kaya Stechly** and…" (the published ICML/PMLR order). Names were otherwise correct.

**4. `Tuisov2025` — title decision (you asked me to act).** I updated the title to the **current** arXiv version, since that is what anyone opening arXiv:2501.18784 now sees:
- → "Successor-Generator Planning with LLM-generated Heuristics"
- (The original v1 title was "LLM-Generated Heuristics for AI Planning: Do We Even Need Domain-Independence Anymore?") Authors were already corrected in the Chapter 3 round (Alexander Tuisov, Yonatan Vernik, Alexander Shleyfman). The chapter prose still reads correctly with either title.

---

## Complete audit table (all 47 entries)

Legend: ✅ verified correct · 🔧 fixed (this audit) · 🛠️ fixed (earlier chapter round)

| # | Key | Authors / status | Result |
|---|---|---|---|
| 1 | `Vallati2021` | Vallati, Chrpa, McCluskey, Hutter | 🛠️ DOI fixed (Ch1) |
| 2 | `Vallati2015` | Vallati, Hutter, Chrpa, McCluskey | 🛠️ pages added (Ch1) |
| 3 | `McCluskey2017` | McCluskey, Vaquero, Vallati | ✅ |
| 4 | `Kambhampati2024` | Kambhampati, Valmeekam, Guan, **Verma, Stechly**, Bhambri, Saldyt, Murthy | 🔧 author order |
| 5 | `Valmeekam2023` | Valmeekam, Olmo, Sreedharan, Kambhampati | ✅ (year note ▼) |
| 6 | `Elis2025` | Daniel Elis | ✅ |
| 7 | `Georgievski2025` | Georgievski, Elis, Vallati | ✅ |
| 8 | `Oswald2024` | Oswald, Srinivas, Kokel, Lee, Katz, Sohrabi | ✅ |
| 9 | `Guan2023` | Guan, Valmeekam, Sreedharan, Kambhampati | ✅ |
| 10 | `Smirnov2024` | Smirnov, Joublin, Ceravola, Gienger | ✅ |
| 11 | `Casciani2025` | Casciani, De Giacomo, Marrella, Weinhuber | 🛠️ authors fixed (Ch1) |
| 12 | `Huang2025` | Cassie Huang, Li Zhang | 🛠️ authors fixed (Ch1) |
| 13 | `Tantakoun2025` | Marcus Tantakoun, Muise, Zhu | 🛠️ author fixed (Ch3) |
| 14 | `Bercher2025` | Bercher, Sarath Sreedharan, Vallati | 🛠️ author fixed (Ch3) |
| 15 | `Stein2025` | Stein, Fišer, Hoffmann, Koller | ✅ |
| 16 | `Tuisov2025` | Alexander Tuisov, Yonatan Vernik, Shleyfman | 🔧 title · 🛠️ authors (Ch3) |
| 17 | `Vallati2025` | Vallati, Barták, Chrpa, McCluskey, Petrick | ✅ |
| 18 | `Franco2019` | Franco, Vallati, Lindsay, McCluskey | ✅ (verified this pass) |
| 19 | `Alarnaouti2023` | Alarnaouti, Baryannis, Vallati | ✅ |
| 20 | `McDermott1998` | McDermott, Ghallab, Howe, Knoblock, Ram, Veloso, Weld, Wilkins | ✅ |
| 21 | `HoweDahlman2002` | Howe, Dahlman | ✅ |
| 22 | `RiddleHolteBarley2011` | Riddle, Holte, Barley | ✅ |
| 23 | `Helmert2009` | Malte Helmert | ✅ |
| 24 | `Vaswani2017` | Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin | ✅ (page note ▼) |
| 25 | `Zhao2023` | Zhao, Zhou, Li, Tang, **Xiaolei Wang**, Hou, Min, Zhang, Zhang, Dong, et al. | 🔧 author name |
| 26 | `Minaee2024` | Minaee, Mikolov, Nikzad, Chenaghlu, Socher, Amatriain, Gao | ✅ |
| 27 | `Georgievski2023` | Ilche Georgievski | 🛠️ title fixed (Ch2) |
| 28 | `Pallagani2024` | Pallagani, Muppasani, **Kaushik Roy**, Fabiano, Loreggia, **Keerthiram Murugesan**, Srivastava, Rossi, Horesh, Sheth | 🛠️ authors fixed (Ch3) |
| 29 | `GhallabNauTraverso2004` | Ghallab, Nau, Traverso | ✅ |
| 30 | `RussellNorvig2021` | Russell, Norvig | ✅ |
| 31 | `FoxLong2003` | Fox, Long | ✅ |
| 32 | `BonetGeffner2001` | Bonet, Geffner | ✅ |
| 33 | `HoffmannNebel2001` | Hoffmann, Nebel | ✅ |
| 34 | `Helmert2006` | Malte Helmert | ✅ |
| 35 | `RichterWestphal2010` | Richter, Westphal | ✅ |
| 36 | `LipovetzkyGeffner2012` | Lipovetzky, Geffner | ✅ |
| 37 | `LipovetzkyGeffner2017` | Lipovetzky, Geffner | ✅ |
| 38 | `GnadHoffmann2018` | Gnad, Hoffmann | 🛠️ venue/type fixed (Ch2) |
| 39 | `KautzSelman1992` | Kautz, Selman | ✅ |
| 40 | `Rintanen2012` | Jussi Rintanen | ✅ |
| 41 | `Brown2020` | Brown, Mann, Ryder, Subbiah, Kaplan, Dhariwal, Neelakantan, Shyam, Sastry, Askell, et al. | ✅ |
| 42 | `Wei2022` | Wei, Wang, Schuurmans, Bosma, Ichter, Xia, Chi, Le, Zhou | ✅ |
| 43 | `Kojima2022` | Kojima, Gu, Reid, Matsuo, Iwasawa | ✅ |
| 44 | `HoweyLongFox2004` | Howey, Long, Fox | ✅ |
| 45 | `Georgievski2026` | Georgievski, Alnazer | ✅ |
| 46 | `Merkel2014` | Dirk Merkel | ✅ |
| 47 | `Cassano2023` | **Cassano, Li, Sethi, Shinn, Brennan-Jones, Lozhkov, Anderson, Guha** | 🔧 title + authors |

*(`Chrpa2020` was removed in the Chapter 3 round — it was uncited and malformed.)*

---

## Honest caveats and minor items (your call — not changed)

These are not errors; I'm flagging them for transparency rather than changing debatable details.

1. **`Cassano2023` author count** — I used the 8-author arXiv-preprint list. If you cite the published COLM 2024 version, verify/extend the list. (The previous list was simply the wrong paper's, so this is already a large improvement.)
2. **`Valmeekam2023` year** — the `booktitle` says "NeurIPS **2022** … Workshop" but `year = {2023}`. For internal consistency consider `year = {2022}` (the workshop and the original arXiv are Dec 2022). Some cite it as 2023; your choice.
3. **`Vaswani2017` pages** — listed as 6000–6010; also commonly cited as 5998–6008 (same paper, different proceedings pagination). Either is defensible; just be consistent.
4. **Middle names** — a few entries drop middle initials that the source includes (e.g., `Kambhampati2024`: "Lucas Saldyt" vs "Lucas Paul Saldyt"; "Anil Murthy" vs "Anil B Murthy"). This is acceptable bibliographic practice and was left as-is.
5. **Entries I relied on as canonical** — the foundational textbooks/reports and the well-known 1–2-author planning papers (`GhallabNauTraverso2004`, `RussellNorvig2021`, `McDermott1998`, `BonetGeffner2001`, `HoffmannNebel2001`, `FoxLong2003`, `Helmert2006/2009`, `KautzSelman1992`, `Rintanen2012`, `Lipovetzky*`, `RichterWestphal2010`, `HoweDahlman2002`, `Merkel2014`) were confirmed by existence + venue in the chapter rounds; their (short) author lists are correct.

---

## Integrity check

- The bibliography contains **47 entries**, all well-formed; the `@Comment{jabref-meta…}` trailer is intact.
- Every `\cite` key used in Chapters 1–6 still resolves to a live entry (the audit changed only author/title/venue fields and removed one *uncited* entry — no citation keys were affected).
- All edits are non-structural; nothing in the LaTeX build is affected.

## Recommendation

The bibliography is now in good shape. Two things to close out:
1. **`Cassano2023`:** confirm the author list against the exact version you cite (caveat 1).
2. **Recompile** and skim the rendered "References" section once, end to end — now that the names are correct, a final visual pass is worth it. (I can't run `biber` here.)

Going forward, the chapters you've already had me review (1–3) are reference-clean. When we continue to Chapters 4–6, I'll keep verifying any *new* citations they introduce, but the core bibliography is now audited.

---

## Sources used in this audit pass
- *Can It Edit?* (Cassano et al.), arXiv:2312.12450 — https://arxiv.org/abs/2312.12450 · authors via https://huggingface.co/papers/2312.12450
- *A Survey of Large Language Models* (Zhao et al.), arXiv:2303.18223 — https://arxiv.org/abs/2303.18223
- *Position: LLMs Can't Plan…* (Kambhampati et al.), ICML 2024 (PMLR v235) — https://proceedings.mlr.press/v235/kambhampati24a.html
- *Successor-Generator Planning with LLM-generated Heuristics* (Tuisov, Vernik, Shleyfman), arXiv:2501.18784 — https://arxiv.org/abs/2501.18784
- *Improving Planning Performance in PDDL+ Domains via Automated Predicate Reformulation* (Franco, Vallati, Lindsay, McCluskey), ICCS 2019 — https://link.springer.com/chapter/10.1007/978-3-030-22750-0_42
- (Plus all primary sources cited in the Chapter 1–3 review documents.)
