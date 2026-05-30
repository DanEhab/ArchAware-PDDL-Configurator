# S0.8 — Key Observations for Stage 0 (Baseline)

This section presents and interprets the key findings from the Stage 0 Baseline experiment. These observations serve two purposes: (1) they characterise the difficulty landscape against which all subsequent LLM-generated domain modifications will be measured, and (2) they establish the planner-specific behavioural baselines that motivate the architecture-aware prompt design in Stage 2.

All 300 runs (4 planners × 5 domains × 15 instances) completed successfully within **5 hours 14 minutes** of total pipeline time. No runs produced a MEMOUT or FAILURE status; the only two outcomes observed were SUCCESS (168 runs, 56.0%) and TIMEOUT (132 runs, 44.0%).

---

## Observation 1 — BFWS Achieved the Highest Solve Rate (85.3%)

**Finding:** BFWS (LAPKT Best-First Width Search, Preference configuration) achieved the highest overall solve rate at **85.33%** (64 out of 75 runs), outperforming the second-best planner, LAMA, by nearly 15 percentage points.

**Architectural Explanation:** BFWS uses a *width-based* search strategy that explores the state space by tracking the novelty of each newly encountered state. Rather than relying solely on domain-specific heuristics (which may be poorly informed for certain domains), BFWS systematically prioritises states that contain previously unseen combinations of variable assignments. This novelty-based approach gives BFWS a structural advantage on domains where traditional heuristic guidance is weak or misleading. Specifically, BFWS was the IPC 2018 Agile Track winner, which means it was specifically optimised for quickly finding *any* solution rather than an optimal one — a strong fit for this experiment's time-limited setting (360-second timeout).

**Confirming Evidence:**
- BFWS achieved **15/15** coverage on three domains (visitall, depots, barman), meaning it solved every single instance in those domains.
- BFWS reported significantly fewer states expanded (mean: 24,395) compared to LAMA (176,143) and DecStar (362,984), indicating that its novelty-based pruning explored far fewer unnecessary states.
- Even on the hardest domain (snake, 31.7% overall solve rate), BFWS solved 8 out of 15 instances — more than any other planner.

---

## Observation 2 — Madagascar Had the Lowest Solve Rate (33.3%)

**Finding:** Madagascar achieved the lowest overall solve rate at **33.33%** (25 out of 75 runs), narrowly below DecStar's 34.67%.

**Architectural Explanation:** Madagascar is fundamentally different from the other three planners in this experiment. While BFWS, LAMA, and DecStar are all *state-space search* planners that explicitly explore the reachable state space using heuristics, Madagascar is a *SAT-based* planner. It translates the planning problem into a series of Boolean satisfiability (SAT) formulas — one formula for each possible plan length — and then solves them using a SAT solver. This approach has both strengths and weaknesses:

- **Strength:** When a short plan exists, Madagascar can find it extremely quickly because SAT solvers are highly optimised for constraint propagation. This explains why Madagascar was the *fastest planner on depots* (mean wall time: 0.58s), a domain where short plans are common.
- **Weakness:** When the optimal plan length is long or unknown, Madagascar must iteratively try formulas for plan lengths 1, 2, 3, ..., *k*, which becomes computationally prohibitive. This is why Madagascar completely failed on ricochet-robots (0/15) — a domain requiring long action sequences — and on visitall (0/15), which requires visiting every node in a grid.

Additionally, Madagascar's SAT encoding grows quadratically with the number of ground actions, making it particularly vulnerable to domains with large action spaces.

---

## Observation 3 — Depots Was the Easiest Domain; Snake Was the Hardest

**Finding:** Across all four planners, depots had a solve rate of **98.3%** (59/60 runs), while snake had a solve rate of just **31.7%** (19/60 runs).

**Domain Difficulty Ranking** (from hardest to easiest):

| Rank | Domain | Solve Rate | Fastest Planner | Fastest Avg Time |
|------|--------|-----------|----------------|-----------------|
| 1 (hardest) | Snake | 31.7% | Madagascar (81.6s) | — |
| 2 | Ricochet-Robots | 36.7% | DecStar (67.1s) | — |
| 3 | Visitall | 50.0% | BFWS (17.6s) | — |
| 4 | Barman | 63.3% | LAMA (3.6s) | — |
| 5 (easiest) | Depots | 98.3% | Madagascar (0.6s) | — |

**Interpretation:**

- **Depots** (IPC 2002) is a well-studied logistics domain with a relatively small and well-structured state space. Its 3-level type hierarchy (`place → {depot, distributor}`, `locatable → {truck, hoist, pallet, crate}`) provides strong typing constraints that all planners can exploit effectively. Out of 60 runs, 59 were successful, with the only TIMEOUT coming from DecStar on a single instance. Among the successful runs, the longest solve time was a 53-second run by DecStar, while the vast majority of runs across all planners finished in under 14 seconds.

- **Snake** (IPC 2018) is hard because it features untyped PDDL, negative preconditions, and a high density of dead-end states. When a snake makes a wrong move, there is often no way to undo it (the tail blocks the path), creating irreversible state transitions that cause planners to waste time exploring unreachable parts of the state space. Even the best planner on snake (BFWS with 8/15) had a mean solve time of 145 seconds, indicating that even successful solves required substantial computation.

- **Ricochet-Robots** (IPC 2023) is a modern domain that models sliding pieces on a grid with walls. It requires long action sequences because pieces slide until they hit a wall, and achieving the goal position often requires using other pieces as blockers — a form of multi-agent coordination that most planners find challenging.

---

## Observation 4 — Three Domain-Planner Combinations Are Completely Unsolvable (0/15)

**Finding:** Three specific (domain, planner) pairs produced zero successful solves out of 15 attempts:

| Domain | Planner | Coverage | All Timeout |
|--------|---------|----------|------------|
| Visitall | DecStar | 0/15 | Yes |
| Visitall | Madagascar | 0/15 | Yes |
| Ricochet-Robots | Madagascar | 0/15 | Yes |

**Interpretation:**

- **Visitall + DecStar:** DecStar uses *star-topology decomposition*, which decomposes the planning task into a central factor and several leaf factors that can be explored somewhat independently. However, visitall's structure — a single agent that must visit every cell in a grid — does not decompose well into a star topology. There is only one "actor" (the agent), and every cell is interconnected. This means DecStar's primary algorithmic advantage (decomposed search) provides no benefit, and its overhead from the decomposition analysis actually makes it *slower* than a straightforward search.

- **Visitall + Madagascar:** Visitall requires visiting all grid cells, resulting in plan lengths proportional to the grid size (often 50–100+ actions). Madagascar's SAT encoding for such long plans creates extremely large formulas that exceed the time limit.

- **Ricochet-Robots + Madagascar:** Similar to visitall, ricochet-robots requires long action sequences due to the sliding mechanic. The SAT-based encoding becomes intractable for plan lengths beyond approximately 20–30 steps.

These three zero-coverage combinations are important because they represent fundamental architectural incompatibilities. They are carried forward into Stage 3 (Feedback Loop) as "always-timeout triples" and excluded from the contestable improvement analysis.

---

## Observation 5 — Seven Domain-Planner Combinations Are Trivially Easy (15/15)

**Finding:** Seven (domain, planner) pairs achieved perfect 15/15 coverage. Of these, four had mean wall-clock times below 5 seconds, qualifying as "trivially easy":

| Domain | Planner | Coverage | Mean Wall Time | Trivially Easy |
|--------|---------|----------|---------------|---------------|
| Depots | Madagascar | 15/15 | 0.58s | Yes |
| Depots | LAMA | 15/15 | 1.99s | Yes |
| Depots | BFWS | 15/15 | 3.13s | Yes |
| Barman | LAMA | 15/15 | 3.62s | Yes |
| Visitall | BFWS | 15/15 | 17.57s | No |
| Visitall | LAMA | 15/15 | 44.01s | No |
| Barman | BFWS | 15/15 | 53.23s | No |

**Interpretation:** The four trivially easy combinations (all under 5 seconds) suggest that for these (domain, planner) pairs, the baseline PDDL domain model already provides excellent guidance to the planner. This means there is relatively *less room for improvement* through domain reordering in Stage 2 — the planner already finds solutions quickly, so any gains from restructuring the domain file will be small in absolute terms. However, even small improvements in plan *quality* (cost) could still be meaningful, which is why the IPC score metric captures quality improvements even when coverage is already at 15/15.

The three non-trivial 15/15 combinations (visitall+BFWS at 17.6s, visitall+LAMA at 44.0s, barman+BFWS at 53.2s) indicate that the planner *eventually* solves all instances but takes significant time. These represent the most interesting targets for LLM-based optimisation: if the domain model can be restructured to help the planner find solutions faster, these solve times could drop substantially.

---

## Observation 6 — N/A Distribution Aligns Perfectly with Planner Architecture

**Finding:** The pattern of missing (N/A) metric values follows directly from each planner's underlying algorithm:

| Metric | BFWS | LAMA | DecStar | Madagascar |
|--------|------|------|---------|-----------|
| PlanCost | 0/64 | 0/53 | 0/26 | 0/25 |
| Runtime_internal_s | 0/64 | 0/53 | 0/26 | 2/25 |
| StatesExpanded | 0/64 | 0/53 | 0/26 | **25/25** |
| StatesGenerated | 0/64 | 0/53 | 0/26 | **25/25** |
| StatesEvaluated | **64/64** | 0/53 | 0/26 | **25/25** |
| PeakMemoryKB | **64/64** | 0/53 | 0/26 | **25/25** |

**Interpretation:** This distribution is a direct consequence of each planner's algorithmic paradigm:

- **LAMA** (Fast Downward, LAMA-first configuration) is a classic *heuristic forward-search* planner. It reports all six metrics because the Fast Downward framework tracks every aspect of the search process, including "Evaluated X states," "Expanded X states," "Generated X states," and "Peak memory: X KB," all in its standard output format.

- **DecStar** (also built on the Fast Downward framework) reports the same metrics as LAMA because it uses the same logging infrastructure. Despite its unique *decoupled search* algorithm, the underlying framework still tracks states expanded, generated, evaluated, and peak memory usage.

- **BFWS** (LAPKT framework) tracks states expanded and generated because these are fundamental to any search algorithm. However, BFWS does *not* report "StatesEvaluated" or "PeakMemoryKB" because the LAPKT framework uses different internal terminology and logging conventions. BFWS tracks "nodes expanded" and "nodes generated" but does not separately count "evaluated" states (in BFWS, a node is evaluated and expanded in a single step, unlike Fast Downward which separates evaluation from expansion). Similarly, LAPKT does not output peak memory usage in the same format.

- **Madagascar** reports *none* of the state-based metrics (StatesExpanded, StatesGenerated, StatesEvaluated, PeakMemoryKB) because it is a *SAT-based* planner. Madagascar does not explore a state space at all — it converts the planning problem into propositional logic formulas and delegates solving to a SAT solver. Concepts like "states expanded" or "states evaluated" simply do not apply to the SAT solving paradigm. The 2 N/A values for Runtime_internal_s arise from cases where Madagascar's internal timing output could not be parsed (the `total time` field was empty or malformed).

This metric availability pattern is important for the thesis because it demonstrates that the choice of planner architecture fundamentally determines what performance data can be collected, which in turn constrains the types of cross-planner comparisons that are valid.

---

## Observation 7 — Strong Positive Correlation Between Runtime and Plan Cost (for Most Planners)

**Finding:** Across all 168 successful runs, there is a strong positive Spearman rank correlation between runtime and plan cost (ρ = 0.6306, p < 0.001), but the strength varies substantially by planner:

| Planner | n | Spearman ρ | Interpretation |
|---------|---|-----------|---------------|
| Overall | 168 | 0.6306 | Strong positive |
| DecStar | 26 | 0.8971 | Very strong positive |
| Madagascar | 25 | 0.8744 | Very strong positive |
| LAMA | 53 | 0.6882 | Moderate-to-strong positive |
| BFWS | 64 | 0.3480 | Weak positive |

**Interpretation:** The general trend — harder instances take longer *and* produce more expensive plans — is expected. When instances are more complex (e.g., larger state spaces, more objects, deeper goal structures), planners need more time to find solutions, and the solutions they find tend to involve more actions (higher cost).

*(Note on Methodology: We use the **Spearman** rank correlation rather than the standard **Pearson** correlation because the relationship between AI planning runtime and plan cost is highly non-linear. Runtime often increases exponentially as problems get harder, while plan cost may only increase linearly. Pearson assumes a straight-line relationship and would be skewed by the exponential spikes in runtime. Spearman, however, compares the **ranks** of the values (e.g., "does the 3rd longest run produce the 3rd most expensive plan?"), making it robust to these non-linear, exponential scaling effects inherent to state-space search.)*

However, the per-planner breakdown reveals important architectural differences:

- **DecStar and Madagascar** show very strong correlations (ρ > 0.87), meaning that when these planners take longer, they almost always produce proportionally worse plans. This suggests that these planners do not benefit much from additional search time — they either find good solutions quickly or struggle extensively.

- **BFWS** shows a weak correlation (ρ = 0.35), meaning that BFWS sometimes takes a long time but still produces relatively good plans. This is consistent with width-based search: BFWS may explore many states (taking time) but the novelty heuristic still guides it toward states that lead to low-cost plans. In other words, BFWS's search effort is less "wasted" than that of other planners.

- **LAMA** falls in between (ρ = 0.69), consistent with its multi-heuristic approach that balances speed and quality.

This observation is relevant for the thesis because it suggests that the potential benefit of domain reordering may differ by planner. If a reordered domain helps BFWS explore fewer states, the resulting plan might be both faster *and* cheaper. For DecStar and Madagascar, reducing solve time through reordering is more likely to also improve plan quality, since the two metrics are tightly coupled.

---

## Observation 8 — High Runtime Variation Within Domain-Planner Pairs

**Finding:** There is substantial variation in runtime between instances within the same (domain, planner) pair. The coefficient of variation (CV = standard deviation / mean) ranges from 0.31 to 2.57:

**Top 5 highest-variation pairs:**

| Domain | Planner | n | Mean (s) | Std (s) | CV | Min (s) | Max (s) |
|--------|---------|---|---------|--------|------|---------|---------|
| Depots | DecStar | 14 | 5.35 | 13.74 | 2.57 | 0.86 | 53.04 |
| Depots | BFWS | 15 | 3.13 | 6.13 | 1.95 | 0.58 | 23.72 |
| Snake | Madagascar | 6 | 81.59 | 112.90 | 1.38 | 5.14 | 308.22 |
| Ricochet-Robots | DecStar | 5 | 67.11 | 91.87 | 1.37 | 7.34 | 226.60 |
| Snake | LAMA | 2 | 87.26 | 113.30 | 1.30 | 7.14 | 167.37 |

**Lowest-variation pair:**

| Domain | Planner | n | Mean (s) | Std (s) | CV | Min (s) | Max (s) |
|--------|---------|---|---------|--------|------|---------|---------|
| Depots | Madagascar | 15 | 0.58 | 0.18 | 0.31 | 0.41 | 1.06 |

**Interpretation:** The high CV values (often exceeding 1.0) indicate that within any given domain-planner pair, some instances are orders of magnitude harder than others. For example, in the depots-DecStar pair, the easiest instance took 0.86 seconds while the hardest took 53.04 seconds — a 62× difference. This extreme variation arises because planning instance difficulty depends on structural properties like the number of objects, the depth of the goal condition, and the branching factor of the state space, which vary significantly across the 15 selected instances.

This high within-pair variation has a critical methodological implication for the thesis: when comparing Stage 0 (baseline) performance against LLM-modified domain performance in Stages 2 and 3, it is essential to compare performance *on the same instances*. A simple comparison of average solve times would be misleading because the instance-level difficulty dominates the signal. This is exactly why the improvement detection framework (Stage 2) uses a paired Wilcoxon signed-rank test — it accounts for instance-level pairing by comparing each instance's baseline performance directly against its modified-domain performance, isolating the effect of the domain modification from the effect of instance difficulty.

The lowest-variation pair (depots-Madagascar, CV = 0.31) is notable because Madagascar solves all 15 depots instances in under 1.06 seconds with very consistent timing. This is characteristic of SAT-based planners on well-structured domains: once the SAT encoding is feasible, the solver's performance is relatively predictable and instance-insensitive.
