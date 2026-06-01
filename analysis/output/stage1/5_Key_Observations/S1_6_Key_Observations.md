# S1.6 — Key Observations for Stage 1 (General Prompt)

This section presents the key findings from the Stage 1 General Prompt experiment. In this stage, four LLMs (GPT-5.4, DeepSeek-R1, Claude Opus 4.6, and Gemini 3.1 Pro) were each given the same generic prompt asking them to reorder a PDDL domain file to improve planner efficiency. The prompt did not provide any planner-specific architectural information — it simply said *"reorder the following PDDL domain file to improve AI planner efficiency."* Each LLM processed all 5 domains, producing 20 modified domain files in total. After validation, 18 of the 20 files passed and were tested across all 4 planners × 15 instances, yielding 1,080 planner runs.

---

## Observation 1 — All LLMs Successfully Generated Valid PDDL (100% API, 90% Validation)

**Finding:** All 20 LLM API calls (4 LLMs × 5 domains) succeeded without any API errors. Every LLM returned a complete response containing a syntactically valid PDDL domain file. Of these 20 responses, 18 (90%) passed the full four-stage validation pipeline (V1 → V2 → V3 → V4) and were classified as VALID.

**Breakdown:**

| Validation Stage | Purpose | Pass Count | Fail Count |
|-----------------|---------|-----------|-----------|
| V1: Extraction | Extract PDDL `(define ...)` block | 20/20 | 0 |
| V2: Syntax (VAL) | Check PDDL syntax via VAL tool | 20/20 | 0 |
| V3: Identity | Verify LLM actually changed something | 18/20 | 2 |
| V4: Semantic | Confirm no illegal logic changes | 18/18 | 0 |

**Interpretation:** The 100% extraction and syntax pass rate (V1 + V2) is a strong indicator that modern LLMs have internalised the PDDL grammar. When explicitly told to output "only a valid reordered PDDL domain file," all four models complied perfectly. None introduced syntax errors, which would have been caught by the VAL tool in V2.

The 100% V4 pass rate (0 semantic violations out of 18 files that reached V4) is equally significant: it means that when LLMs did make changes, they *always* preserved the logical meaning of the domain. No LLM accidentally renamed a predicate, added an extra precondition, or removed an effect. This suggests that LLMs understand the distinction between syntactic ordering (safe to change) and semantic content (must not change), at least when the prompt explicitly warns them not to alter semantics.

---

## Observation 2 — DeepSeek-R1 Was Rejected for 2 Domains Because It Returned the Original Unchanged

**Finding:** The only two validation failures came from DeepSeek-R1, which failed at V3 (Identity Check) for ricochet-robots and barman. The V3 check compares the LLM's output against the original domain file after normalising whitespace, and rejects the output if it is identical — meaning the LLM made zero changes to the file.

**What happened:** DeepSeek-R1 received the ricochet-robots and barman domain files and, after its internal reasoning process, decided that the existing ordering was already optimal (or close enough) and returned the domain file unchanged. The validation pipeline correctly identified these as "no-transformation" outputs and rejected them, since running planners on an identical domain file would produce results indistinguishable from the Stage 0 baseline.

**Why this matters:** This behaviour reveals an important difference between conservative and aggressive LLMs when it comes to domain reordering:

- **DeepSeek-R1** is the most *conservative* model in this experiment. Its "chain-of-thought" reasoning architecture (DeepSeek-R1 uses a reasoning model that thinks before answering) apparently led it to conclude that some domains do not benefit from reordering. While this may be correct in some cases, it resulted in 2/5 = 40% of its domains being unusable for the experiment.

- **GPT-5.4, Claude 4.6, and Gemini 3.1** were all more *aggressive*: they always made at least one change to every domain file, achieving a 100% validation pass rate (5/5 each). This does not necessarily mean their reorderings were better — only that they always attempted a modification.

This observation is relevant for the thesis because it raises a design question for Stage 2 (Architecture-Aware): should the prompt encourage the LLM to always make changes, or should conservative "no change needed" responses be accepted as valid? The current pipeline rejects identity outputs, which penalises conservative models like DeepSeek-R1.

---

## Observation 3 — Preconditions Were the Most Frequently Reordered Component (88.9%)

**Finding:** Across the 18 valid domain files, the PDDL component most frequently reordered was *preconditions* (reordered in 16 out of 18 files, or 88.9%). The full frequency ranking is:

| Component | Times Reordered | Percentage |
|-----------|----------------|-----------|
| Preconditions | 16 | 88.9% |
| Actions | 12 | 66.7% |
| Add Effects | 11 | 61.1% |
| Delete Effects | 6 | 33.3% |
| Predicates | 4 | 22.2% |
| Requirements | 0 | 0.0% |
| Types | 0 | 0.0% |
| Functions | 0 | 0.0% |
| Parameters | 0 | 0.0% |

**Interpretation:** This frequency distribution reveals what LLMs "believe" matters most for planner performance when given no architecture-specific guidance. The clear hierarchy — preconditions > actions > effects > predicates > everything else — aligns surprisingly well with the planning literature:

- **Preconditions (88.9%):** In heuristic forward-search planners like LAMA and DecStar, preconditions are evaluated during *successor generation*. When the planner checks whether an action is applicable in a given state, it tests each precondition in order from first to last. If an early precondition fails (returns false), the planner can immediately skip the action without evaluating the remaining preconditions. This is called *early pruning*. By placing the most restrictive (most frequently false) preconditions first, the LLM can reduce the number of precondition checks the planner performs, thereby speeding up search.

- **Actions (66.7%):** The order of actions in the PDDL file determines the order in which the planner considers them during successor generation. If the most "useful" actions (e.g., goal-achieving actions) are listed first, the planner may find solutions faster because it explores promising branches of the search tree earlier.

- **Effects (61.1% add, 33.3% delete):** While effect ordering has less direct impact on most planners (effects are typically applied as a set), some planners process effects sequentially, and the ordering can influence heuristic computation in subtle ways.

- **Parameters (0.0%):** No LLM ever reordered parameters. This is expected because parameter ordering in PDDL is semantically significant — changing `(:action move ?from - location ?to - location)` to `(:action move ?to - location ?from - location)` would break all problem files that reference this action. LLMs correctly recognised this constraint and left parameters untouched.

---

## Observation 4 — No LLM Ever Reordered Requirements, Types, or Functions

**Finding:** Three PDDL components were never reordered by any LLM: requirements (`:requirements`), types (`:types`), and functions (`:functions`). Combined with the observation that parameters were also never reordered, this means 4 out of 9 tracked components were universally left unchanged.

**Interpretation:**

- **Requirements:** The `:requirements` section (e.g., `:strips`, `:typing`, `:equality`) is a declaration of which PDDL features the domain uses. Planners typically parse this section once during initialisation to configure their internal capabilities, and the order of requirements has zero impact on planning performance. LLMs correctly identified this as irrelevant to reorder.

- **Types:** The `:types` section defines the type hierarchy (e.g., `truck hoist pallet crate - locatable`). Type ordering *could* theoretically affect some planners' internal grounding order, but in practice, most planners build a type hierarchy tree regardless of the textual order. LLMs appear to have internalised this knowledge.

- **Functions:** The `:functions` section defines numeric fluents (e.g., `(total-cost)`). Like requirements, these are parsed once and do not affect search ordering. In fact, only 2 of the 5 domains in this experiment even use functions (depots uses `(total-cost)` implicitly), so there was limited opportunity for reordering.

This pattern is architecturally meaningful: LLMs appear to distinguish between "structural/declarative" components (requirements, types, functions) and "operational" components (actions, preconditions, effects) — and they only reorder the operational ones. This demonstrates a genuine understanding of PDDL semantics, not merely random shuffling.

---

## Observation 5 — Claude 4.6 Was the Most Aggressive Reorderer; DeepSeek-R1 Was the Most Conservative

**Finding:** By counting the actual number of individual items reordered (parsed from the detailed diff JSON files), the LLMs showed dramatically different levels of aggressiveness:

| LLM | Total Reordered Items | Avg Per Domain | Valid Domains |
|-----|----------------------|---------------|--------------|
| Claude 4.6 | 33 | 6.6 | 5/5 |
| GPT-5.4 | 31 | 6.2 | 5/5 |
| Gemini 3.1 | 28 | 5.6 | 5/5 |
| DeepSeek-R1 | 9 | 3.0 | 3/5 |

**Interpretation:** Claude 4.6, GPT-5.4, and Gemini 3.1 were all similarly aggressive, making around 30 individual reordering changes each. In stark contrast, they made over three times more changes than DeepSeek-R1. This aggressiveness manifests in specific ways:

- **Claude 4.6** reordered preconditions, actions, add effects, *and* delete effects in most domains. For the barman domain, Claude touched 5 out of 9 component categories, moving predicates, action ordering, preconditions within multiple actions, and effects — a total of 11 individual reorderings in a single domain file.

- **GPT-5.4** showed a similar pattern, additionally reordering predicates in several domains. GPT-5.4 was the only LLM to reorder predicates in visitall, and it reordered the most component categories in the barman domain (5 categories).

- **DeepSeek-R1**, even in the 3 domains where it did make changes, only performed minimal reorderings. For depots, it made just a single precondition reorder. For snake, it reordered actions and preconditions but nothing else. This extreme conservatism, combined with its 2 identity rejections, positions DeepSeek-R1 as the least useful LLM for the general prompt approach.

This observation has direct implications for Stage 2: if the architecture-aware prompt successfully motivates DeepSeek-R1 to be more aggressive in its reorderings, it would provide strong evidence that planner-specific information changes LLM behaviour.

---

## Observation 6 — The Overall Solve Rate Was Not Meaningfully Different from Stage 0

**Finding:** The Stage 1 overall solve rate was **56.57%** (611/1,080 runs), compared to Stage 0's **56.0%** (168/300 runs) — a difference of just **0.57 percentage points**.

**Per-planner comparison:**

| Planner | Stage 0 Solve Rate | Stage 1 Solve Rate | Difference |
|---------|-------------------|-------------------|-----------|
| BFWS | 85.33% | 83.33% | −2.00 pp |
| LAMA | 70.67% | 71.11% | +0.44 pp |
| DecStar | 34.67% | 35.19% | +0.52 pp |
| Madagascar | 33.33% | 36.67% | +3.34 pp |

**Interpretation:** The solve rates are remarkably stable between Stage 0 and Stage 1. No planner showed a change exceeding 3.5 percentage points. This stability is expected and actually *confirms the experimental design*: since Stage 1 only reorders PDDL components without changing the domain's semantics, the set of solvable instances should remain approximately the same. An instance that was fundamentally unsolvable in Stage 0 (e.g., visitall on DecStar) will remain unsolvable regardless of how the domain file is reordered.

The small differences (e.g., BFWS dropping 2 percentage points) are likely due to:
1. **Borderline instances:** Some instances that were solved in 355 seconds in Stage 0 may have been pushed just over the 360-second timeout in Stage 1, or vice versa, depending on how reordering affected the planner's search path.
2. **Non-determinism:** Docker container startup times and OS-level scheduling can introduce small timing variations between runs.

This observation is important for the thesis because it demonstrates that **general (non-architecture-aware) prompt-based reordering does not produce large coverage improvements**. This sets the stage for the key research question: can architecture-aware prompting (Stage 2) do better?

---

## Observation 7 — The Timeout Distribution Mirrored Stage 0 Exactly

**Finding:** The domain and planner timeout patterns in Stage 1 are nearly identical to Stage 0:

**By Domain:**

| Domain | Stage 0 Timeout % | Stage 1 Timeout % |
|--------|------------------|------------------|
| Snake | 68.3% | 69.2% |
| Ricochet-robots | 63.3% | 65.0% |
| Visitall | 50.0% | 50.0% |
| Barman | 36.7% | 34.4% |
| Depots | 1.7% | 1.7% |

**By Planner:**

| Planner | Stage 0 Timeout % | Stage 1 Timeout % |
|---------|------------------|------------------|
| DecStar | 65.3% | 64.8% |
| Madagascar | 66.7% | 63.3% |
| LAMA | 29.3% | 28.9% |
| BFWS | 14.7% | 16.7% |

**Interpretation:** The timeout distribution is virtually unchanged. The same domains (snake, ricochet-robots) remain the hardest, and the same planners (DecStar, Madagascar) continue to time out the most. This reinforces Observation 6: general-purpose reordering does not alter the fundamental difficulty landscape. The structural properties that make snake hard (dead-end states, untyped PDDL) and that make DecStar struggle on visitall (poor star-topology decomposition) are not addressed by simply shuffling the order of PDDL components.

---

## Observation 8 — DeepSeek-R1 Used 2.7× More Output Tokens Than Other LLMs

**Finding:** DeepSeek-R1 consumed dramatically more output tokens than the other three LLMs:

| LLM | Output Tokens | Avg Per Domain | Ratio vs. GPT-5.4 |
|-----|--------------|---------------|-------------------|
| DeepSeek-R1 | 10,201 | 2,040 | 3.15× |
| Claude 4.6 | 3,866 | 773 | 1.19× |
| Gemini 3.1 | 3,541 | 708 | 1.09× |
| GPT-5.4 | 3,239 | 648 | 1.00× |

**Interpretation:** DeepSeek-R1's inflated token count is a direct consequence of its *reasoning model* architecture. Unlike GPT-5.4, Claude 4.6, and Gemini 3.1 (which are standard instruction-following models), DeepSeek-R1 explicitly generates a "chain-of-thought" reasoning trace before producing its final answer. Even though the prompt instructed the LLM to "return ONLY a valid reordered PDDL domain file," DeepSeek-R1 still generated extensive internal reasoning tokens (which are counted in the output token total, even though the final extracted PDDL block was of normal length).

This has a practical implication: DeepSeek-R1 costs approximately 3× more per API call than GPT-5.4 in terms of token usage, yet it produced the *fewest* valid reorderings (3/5 domains, 9 total reordered items). This makes DeepSeek-R1 the least cost-effective model for the general prompt approach in this experiment.

---

## Observation 9 — LLMs Apply Consistent Reordering Strategies Across Domains of Similar Complexity

**Finding:** When comparing the reordering patterns across domains, a clear pattern emerges: LLMs reorder *more components* for complex domains and *fewer components* for simple domains.

| Domain | Avg Components Reordered | Domain Complexity |
|--------|-------------------------|-------------------|
| Barman | 3.3 per LLM | 12 actions, 15 predicates |
| Depots | 2.5 per LLM | 5 actions, 10 predicates |
| Snake | 2.5 per LLM | 5 actions, 7 predicates |
| Ricochet-robots | 2.3 per LLM | 4 actions, 6 predicates |
| Visitall | 0.75 per LLM | 1 action, 3 predicates |

**Interpretation:** Visitall, the simplest domain (only 1 action with 3 preconditions), received the fewest reorderings — most LLMs changed only a single component. This makes sense: with only one action, there is no action ordering to change, and with only 3 preconditions, the number of possible reorderings is limited (3! = 6 permutations). Barman, the most structurally complex domain (12 actions, 15 predicates, complex action interactions involving shakers, shots, and cocktails), received the most reorderings because there are many more components that can be meaningfully rearranged.

This demonstrates that LLMs are not randomly shuffling PDDL components — they are making *domain-aware decisions* about which components to reorder, even without explicit planner-specific guidance.

---

## Observation 10 — The Coverage Matrix Shows LLM-Generated Domains Behave Identically Across All LLMs

**Finding:** When examining the S1-T9 Coverage Matrix, the coverage numbers for a given (domain, planner) pair are remarkably consistent regardless of which LLM generated the domain. For example:

- **Depots × BFWS:** 15/15 for all 4 LLMs (GPT-5.4, Claude 4.6, DeepSeek-R1, Gemini 3.1)
- **Visitall × DecStar:** 0/15 for all 4 LLMs
- **Snake × LAMA:** 2/15 for all 4 LLMs

**Interpretation:** This uniformity confirms that general-purpose reordering — without architecture-specific guidance — produces functionally equivalent domain files from a planner's perspective. While the internal ordering of preconditions and actions differs between LLMs, these differences do not translate into meaningful coverage differences at the instance level.

This finding directly motivates the need for Stage 2 (Architecture-Aware Prompting). If we want reordering to actually *change* planner behaviour — to help a planner solve instances it previously timed out on, or to solve them faster — we need to provide the LLM with specific information about *which* planner will be used and *how* that planner processes the domain file. Generic "improve efficiency" instructions, as used in Stage 1, are insufficient to produce targeted improvements.
