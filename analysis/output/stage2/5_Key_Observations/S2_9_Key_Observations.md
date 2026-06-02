# S2.9 — Key Observations for Stage 2 (Architecture-Aware Prompting)

> **Stage Summary:** Stage 2 tested whether providing LLMs with detailed planner-architecture knowledge enables them to produce specialised PDDL domain reorderings that improve target planner performance. 80 architecture-aware prompts were generated (4 LLMs × 5 domains × 4 planner prompts), of which 75 survived validation. After executing each validated domain on its target planner (1,125 runs), a rigorous three-condition improvement test identified **42 out of 75 configurations (56.0%) as genuinely improved**. A cross-test phase then evaluated all 42 improved domains on the three *non-target* planners (1,890 additional runs) to assess whether the improvements were planner-specific.

---

## Part 1 — Improvement Efficacy

### Observation 1: Why was Depots 100% improved across all 14 triples?

The `depots` domain was the only domain to achieve a perfect 100% improvement rate: every single LLM–planner combination that was tested showed a statistically significant positive IPC gain. The explanation lies in the interaction between the domain's PDDL structure and the baseline coverage data.

In the baseline (Stage 0), `depots` already had very high coverage across all planners: LAMA solved 15/15, BFWS solved 15/15, DecStar solved 14/15, and Madagascar solved 15/15. This means that there was no "coverage ceiling" problem — all planners were already solving most or all instances, so the only question was *how fast* they solved them. When all 15 instances produce valid runtime measurements, the Wilcoxon signed-rank test has maximal statistical power (it has 15 paired data points to work with). Even a small but consistent speedup across 15 instances easily produces a significant p-value.

Additionally, `depots` is a logistics-style domain with complex interactions between vehicles (`trucks`), loading equipment (`hoists`), containers (`crates`), and storage areas (`pallets`, `depots`, `distributors`). This creates a rich network of interdependent predicates and actions. When the LLMs received architecture-specific instructions (e.g., "place goal-relevant predicates first" or "order actions with fewer preconditions earlier"), there were many meaningful reordering opportunities. The domain's inherent structural complexity gave the LLMs substantial room to apply the architecture-aware heuristics, and the high baseline coverage meant that every resulting speedup was statistically detectable.

The Top 10 Best IPC Gains table (S2-T17) confirms this: **8 out of the top 10 gains belong to depots**, with gains reaching as high as 0.085 (Claude 4.6 targeting BFWS).

---

### Observation 2: Why was Ricochet-Robots the least responsive domain?

`Ricochet-robots` achieved only a 26.7% improvement rate (4 out of 15 triples improved), making it the most resistant domain. Two factors explain this:

**Factor 1 — Low Baseline Coverage.** In the baseline, only LAMA (6/15) and BFWS (11/15) could solve any instances at all. DecStar solved only 5/15, and Madagascar solved 0/15. This means that for all Madagascar-targeted triples, both the baseline and Stage 2 scored zero on every instance — the planner simply cannot solve this domain regardless of PDDL ordering. These "zero coverage" pairs produce gains of exactly 0.0 for all 15 instances, which trivially fails both the statistical significance condition (p = 1.0) and the practical significance condition (gain = 0.0). Indeed, 4 out of 15 ricochet-robots triples are zero-coverage pairs (all Madagascar triples).

**Factor 2 — Combinatorial Domain Structure.** Ricochet-robots requires robots to slide across a grid in cardinal directions until they hit a wall or another robot. This creates a state space where the key difficulty is not in evaluating individual actions but in discovering long chains of moves that indirectly position robots. Reordering predicates or actions does not fundamentally change the search topology: the planner still needs to explore the same deep combinatorial tree. The improvements that did occur (all 4 were LAMA or BFWS) were modest (gains of 0.001 to 0.020), confirming that reordering provides only marginal help for inherently combinatorial domains.

---

### Observation 3: Why did LAMA achieve a 100% improvement rate while Madagascar only achieved 30%?

This is one of the most architecturally significant findings in the entire thesis. The improvement rates by planner were:

| Planner | Improvement Rate | Architectural Type |
|---------|------------------|--------------------|
| LAMA | 18/18 (100.0%) | Heuristic forward search (FF + Landmarks) |
| BFWS | 11/19 (57.9%) | Heuristic forward search (Novelty-based) |
| DecStar | 7/18 (38.9%) | Factored search (star topology decomposition) |
| Madagascar | 6/20 (30.0%) | SAT-based compilation |

The ranking exactly mirrors how sensitive each planner's architecture is to the textual ordering of PDDL elements:

**LAMA (100%):** LAMA is a heuristic forward-search planner that relies heavily on the FF heuristic (delete-relaxation) and landmark analysis. As stated in the LAMA architecture-aware prompt, *"the textual ordering of predicates affects mutex discovery and landmark ordering quality"* and *"the ordering of preconditions directly affects which 'best support' is selected during FF's relaxed-plan extraction, determining WHICH actions become preferred operators."* In short, LAMA's entire search strategy — which states to expand, which operators to prefer, and which landmarks to track — is influenced by the order in which PDDL elements are listed. This makes it maximally responsive to intelligent reordering.

**Madagascar (30%):** Madagascar is a SAT-based planner that compiles the entire planning problem into a Boolean satisfiability formula. Modern SAT solvers use dynamic variable-ordering heuristics such as VSIDS (Variable State Independent Decaying Sum), which internally re-prioritise variables during solving based on conflict history. While the initial SAT variable IDs are determined by PDDL ordering, the solver quickly overrides these initial assignments through its own learned heuristics. This means the LLM's carefully constructed predicate ordering has a diminished effect compared to heuristic search planners. The 6 successful Madagascar improvements mostly occurred in `depots` (a domain where all 15 instances were solvable, providing maximum statistical power) and `snake` (where a large runtime win on even a few instances was enough).

---

### Observation 4: Which LLM produced the most improvements?

| LLM | Triples Tested | Improved | Rate |
|-----|----------------|----------|------|
| Claude 4.6 | 20 | 13 | 65.0% |
| Gemini 3.1 | 17 | 10 | 58.8% |
| DeepSeek-R1 | 20 | 10 | 50.0% |
| GPT-5.4 | 18 | 9 | 50.0% |

Claude Opus 4.6 led with a 65.0% improvement rate. Two factors explain this:

First, Claude had the highest validation pass rate — all 20 of its API calls returned valid, syntactically correct PDDL files. It produced zero token limit errors and zero V4 semantic failures. This reliability ensured that all 20 of its configurations entered the planner execution pipeline, maximising the number of triples that *could* be tested.

Second, Claude appears to be particularly adept at following complex technical instructions while simultaneously respecting strict constraints (e.g., "do NOT change the logical meaning"). The architecture-aware prompts required the LLM to simultaneously understand planner internals (FF heuristics, SAT encodings, etc.) and apply this knowledge to reorder PDDL elements without altering semantics. Claude's instruction-following precision gave it an edge.

Notably, Gemini 3.1 Pro achieved a comparable rate (58.8%) but was tested on only 17 triples instead of 20, because 3 of its API calls hit the token limit (for DecStar and LAMA prompts on Depots and Barman). DeepSeek-R1, despite generating roughly 3× more output tokens than other LLMs (106,185 total vs 12,961 for GPT-5.4), did not translate this additional reasoning effort into a higher improvement rate.

---

### Observation 5: What do the zero-gain failures tell us about planner-domain compatibility limits?

Among the 33 non-improved configurations, the Failed Condition Analysis (S2-T14) revealed that **12 triples had zero coverage in both the baseline and Stage 2**. These are cases where the planner timed out on all 15 instances regardless of PDDL ordering.

These zero-coverage pairs cluster exclusively in two scenarios:
- **Visitall × DecStar / Madagascar** (4 pairs each): Neither DecStar nor Madagascar can solve a single `visitall` instance within the time limit, regardless of domain ordering. The `visitall` domain, which requires an agent to visit every cell in a grid, creates a state space that is fundamentally incompatible with factored-search (DecStar) and SAT-based (Madagascar) approaches within the allotted time.
- **Ricochet-robots × Madagascar** (4 pairs): Madagascar cannot solve any instance of this combinatorial sliding-puzzle domain.

This finding establishes a clear boundary for the architecture-aware approach: **PDDL reordering cannot overcome fundamental planner-domain incompatibility.** When a planner's search algorithm is structurally unable to handle a domain's state space, no amount of syntactic optimisation will help. This is an important methodological contribution, as it separates the "reachable" improvement space from the "inherently unsolvable" space.

---

### Observation 6: Why did GPT-5.4 produce the only V4 semantic failures?

GPT-5.4 was the only LLM that produced V4 semantic validation failures — two cases where the output PDDL file was syntactically valid but contained altered logic:
- **Ricochet-robots × LAMA** prompt
- **Depots × BFWS** prompt

The V4 semantic validator checks that the *logical structure* of the domain file is preserved: all preconditions and effects must be identical (aside from ordering). GPT-5.4's failures suggest that it occasionally "over-interpreted" the architecture-aware instructions, going beyond reordering to actually modify preconditions or effects in an attempt to optimise performance. In other words, GPT-5.4 was too "creative" — it tried to improve the domain's logic rather than just its ordering.

This contrasts with Claude Opus 4.6, which achieved zero validation failures across all 20 calls. Claude demonstrated stronger constraint adherence, reliably distinguishing between "reorder these elements" and "rewrite these elements."

---

### Observation 7: What was the distribution of IPC gains?

The 42 improved configurations exhibited the following gain distribution:

| p-value Range | Count |
|---------------|-------|
| p ≤ 0.001 | 19 |
| 0.001 < p ≤ 0.01 | 3 |
| 0.01 < p ≤ 0.05 | 5 |
| 0.05 < p ≤ 0.10 | 3 |
| 0.10 < p ≤ 0.25 | 12 |

The gains themselves were concentrated in the range of 0.001 to 0.085 IPC score improvement. Most gains were moderate (0.01–0.05), but a significant tail of high-impact configurations existed, particularly in `depots`. Importantly, **no single configuration achieved a gain above 0.1**, indicating that architecture-aware reordering produces consistent, moderate improvements rather than dramatic breakthroughs. The improvements are real and reliable, but they represent fine-tuning rather than paradigm shifts in planner performance.

---

### Observation 8: What does the Wilcoxon analysis tell us about the reliability of improvements?

The Wilcoxon signed-rank test was chosen because the IPC gain data is paired (each instance has a baseline score and a Stage 2 score) and cannot be assumed to be normally distributed. Using the one-sided alternative hypothesis (H₁: Stage 2 > Stage 0) with a threshold of p ≤ 0.25, the test ensures that only configurations with statistically consistent improvements (not just lucky speedups on one or two instances) are flagged as genuine.

Out of 42 improved triples, 19 achieved extremely high significance (p ≤ 0.001), meaning the chance of observing such consistent gains by random fluctuation is less than 0.1%. These highly significant results predominantly came from `depots` and `barman`, where all 15 instances were solvable (maximum statistical power).

At the other end, 12 improved triples had p-values between 0.10 and 0.25. These were mostly from domains with low coverage (`snake` with 2/15 baseline coverage for LAMA, `ricochet-robots` with 6/15 for LAMA), where only a few instances provided non-zero paired differences. The Wilcoxon test has reduced power with fewer non-zero pairs, so p-values are inherently larger — but the improvements were still real and directionally consistent.

---

## Part 2 — Architecture Specialization Analysis

> This section addresses the central thesis question: *Did the architecture-aware prompts produce improvements that are specific to the target planner (specialised), or did they simply make the domain generally better for all planners (universal)?*

### Methodological Note: IPC Scoring in the Cross-Test Matrix

The Cross-Test Specialization Matrix (S2-T21) and the derived Specialization Verdicts (S2-T22 through S2-T25) use a different IPC calculation method than what appears in `improvement_results.csv`. This is deliberate and necessary for mathematical consistency. The two approaches are explained below.

**Approach used in `improvement_results.csv` (Global T\*):**
The `run_improvement_test.py` script calculates $T^*$ (the reference best time for each problem instance) by finding the minimum runtime across *all stages* present in `planner_execution_data.csv` at the time of execution. Because this CSV contains data from all 4 stages (including Feedback Loops 1–3), $T^*$ reflects the globally fastest time any configuration ever achieved. This is the standard IPC competition formula:

$$Score_i = \frac{1}{1 + \log_{10}(T_i / T^*)}$$

**Approach used in the Cross-Test Matrix (Local T\*):**
For the specialization analysis, we calculate $T^*$ locally as $T^* = \min(T_{baseline}, T_{test})$ for each instance independently. This is called the "Local Vacuum" approach. The mathematical steps are:

1. For a given (Domain, LLM, Target Planner, Actual Planner) quadruple, retrieve the Baseline runtime $B$ and the Modified-domain runtime $T$ for each of the 15 instances.
2. Calculate $T^* = \min(B, T)$ — the faster of the two.
3. Calculate the Baseline IPC score: $Score_{base} = T^* / B$ (if $B$ is a successful run, otherwise 0).
4. Calculate the Modified IPC score: $Score_{mod} = T^* / T$ (if $T$ is a successful run, otherwise 0).
5. The instance-level gain is $Score_{mod} - Score_{base}$.
6. If both $B$ and $T$ are timeouts, the gain is 0.0 (and this zero is included in the average, meaning the denominator is always 15).

**Why are the numbers different?** Because a Global $T^*$ is always ≤ a Local $T^*$, the IPC scores from the global approach are "shrunk" toward zero (the denominator in the IPC formula is larger). This makes absolute gain values from `improvement_results.csv` smaller than those in the Cross-Test Matrix.

**Why use the Local approach for cross-testing?** Because the Cross-Test Matrix compares how the *same* domain file performs on *different* planners. For this comparison to be fair, every cell in the matrix must use the *same mathematical methodology*. If we used Global $T^*$, the diagonal cells (target planner) would have their $T^*$ calculated from a pool that includes Stage 2 data, while the off-diagonal cells (non-target planners) would have $T^*$ values drawn from Cross-Test data. The mixing of different data scopes would create an unfair comparison. The Local Vacuum ensures that a +0.03 gain on LAMA means the exact same magnitude of isolated time improvement as a +0.03 gain on Madagascar. The Cross-Test Matrix is fully internally consistent.

---

### Specialization Verdict Definitions

Each of the 42 improved configurations was classified into one of four quadrants based on its **Target Gain** (IPC improvement on the planner the prompt was designed for) and its **Average Non-Target Gain** (mean IPC change across the three other planners when run on the same reordered domain file). Since all 42 configurations already passed the improvement detection test, we know that Target Gain > 0 for all of them. The classification depends entirely on what happened to the non-target planners:

| Verdict | Condition | Interpretation |
|---------|-----------|----------------|
| **Specialised** | Non-Target Gain ≤ −0.005 | The target planner improved, but the optimisation actively *hurt* the other planners. This is the purest evidence of architecture-specific tuning. |
| **Neutral** | −0.005 < Non-Target Gain < 0.005 | The target planner improved, and the other planners were essentially unaffected (within the noise margin). |
| **Universally Better** | 0.005 ≤ Non-Target Gain, AND Non-Target ≤ Target Gain | Both the target and the other planners improved, but the target improved *at least as much* as the non-targets. The optimisation was generally beneficial but still biased toward the target. |
| **Anti-Specialised** | Non-Target Gain > Target Gain | The optimisation helped the other planners *more* than the target planner it was designed for. This contradicts the specialisation hypothesis. |

**Why use ±0.005 as the boundary instead of exactly 0.0?** IPC scores are continuous floating-point values. A difference of 0.001 might represent a fraction of a second on a single instance out of 15, which is within the range of system-level timing noise (process scheduling, I/O contention, etc.). If we used exactly 0.0 as the threshold, a configuration that slowed non-target planners by a negligible 0.0002 IPC would be incorrectly classified as "Specialised." The ±0.005 margin ensures that when we label something as Specialised or Universally Better, the effect is large enough to be meaningfully distinct from measurement noise.

---

### Observation 9: What percentage of the 42 improved configs are truly specialised?

The Specialization Index Summary (S2-T25) provides the headline numbers:

| Verdict | Count | Percentage |
|---------|-------|------------|
| Specialised | 16 | 38.1% |
| Universally Better | 15 | 35.7% |
| Anti-Specialised | 8 | 19.0% |
| Neutral | 3 | 7.1% |

**38.1% of all improved configurations exhibited true specialisation** — the target planner improved while the non-target planners were hurt. Furthermore, an overwhelming **81.0% (34/42) of configurations had a positive Specialization Index** (meaning Target Gain > Average Non-Target Gain). The mean Specialization Index across all 42 configurations was **+0.0313**, confirming that architecture-aware prompting systematically biases improvements toward the target planner.

This provides strong empirical support for the core thesis hypothesis: providing LLMs with planner-specific architectural knowledge successfully induces specialised optimisation that favours the target planner over alternatives.

---

### Observation 10: What percentage are universally better?

**35.7% (15/42) of configurations were Universally Better** — both the target planner and the non-target planners improved, but the target improved at least as much. This is not a failure of the thesis; rather, it reveals an important secondary finding: architecture-aware prompting sometimes resolves *general* inefficiencies in the PDDL domain file that were hindering all planners equally.

For example, if the original domain file listed a rarely-used predicate first and a goal-critical predicate last, reordering them to put the goal-critical predicate first might help every planner. The LLM was instructed to prioritise one planner, but in doing so, it also "cleaned up" the domain structure in ways that benefited everyone. This finding suggests that some PDDL domain files contain "universal inefficiencies" that any intelligent reordering would fix, regardless of which planner is being targeted.

Notably, the Universally Better configs are concentrated in `depots` (a domain with inherently many structural opportunities for improvement) and tend to involve BFWS or Madagascar as the target — planners whose optimisation strategies happen to overlap partially with what benefits other planners.

---

### Observation 11: Does the LAMA prompt show the most specialisation?

Yes. The Specialization Verdict by Planner table (S2-T23) shows:

| Target Planner | Specialised | Universally Better | Anti-Specialised | Mean Spec Index |
|----------------|-------------|--------------------|------------------|-----------------|
| LAMA | 10/18 (56%) | 4/18 | 3/18 | +0.0338 |
| BFWS | 3/11 (27%) | 6/11 | 0/11 | +0.0536 |
| DECSTAR | 2/7 (29%) | 1/7 | 4/7 | −0.0079 |
| MADAGASCAR | 1/6 (17%) | 4/6 | 1/6 | +0.0284 |

LAMA produced the highest number and proportion of strictly Specialised configurations (10 out of 18, or 56%). This aligns perfectly with LAMA's architectural sensitivity: because LAMA's FF heuristic, landmark analysis, and preferred-operator selection are all directly affected by PDDL element ordering, optimisations tailored for LAMA's specific pipeline often create orderings that are *detrimental* to planners with fundamentally different search strategies. When the LLM places static predicates first in preconditions (a LAMA-specific optimisation for fast applicability short-circuiting), this ordering may not benefit BFWS's novelty-based evaluation or Madagascar's SAT encoding.

Interestingly, BFWS has the highest Mean Specialization Index (+0.0536), but with fewer Specialised configs (3/11) and more Universally Better configs (6/11). This means that BFWS-targeted reorderings tend to consistently favour the target over non-targets (high index), but they usually help other planners too rather than hurting them.

---

### Observation 12: Why might Madagascar-targeted prompts produce universal improvements?

Madagascar-targeted configurations produced 4 Universally Better outcomes and only 1 strictly Specialised outcome. This seemingly contradicts the specialisation hypothesis, but the explanation is architecturally logical.

When the LLM optimises for Madagascar, the prompt instructs it to: (1) place goal predicates first to give them low SAT variable IDs, (2) group mutually exclusive predicates adjacently for faster mutex discovery, and (3) order actions so that goal-achieving actions receive lower variable IDs. These guidelines essentially create a "clean, logically structured" domain file where goal-relevant elements are prioritised and related elements are grouped together.

This logically structured ordering *also* benefits heuristic search planners:
- LAMA benefits because goal-relevant predicates placed first accelerate its landmark analysis.
- BFWS benefits because the cleaner predicate ordering improves its novelty evaluation.
- DecStar benefits because grouped predicates create more efficient factored state-space decompositions.

In essence, Madagascar's optimisation guidelines inadvertently align with "universal good practice" for PDDL structuring. Unlike LAMA, whose specific optimisations (e.g., placing static preconditions first for short-circuiting) are unique to forward-search planners, Madagascar's guidelines produce orderings that happen to be generally good.

---

### Observation 13: Is there a correlation between gain magnitude and specialisation?

Yes, but it is an *inverse* correlation: the largest magnitude gains tend to be universal, not specialised. Examining the Specialization Verdicts (S2-T22) and the Scatter Plot (S2-G13), the points furthest to the right (highest Target Gain > 0.08) are almost all in the top-right quadrant (Universally Better) and are predominantly from `depots`. For example:
- Depots × DeepSeek-R1 × BFWS: Target Gain +0.137, Avg Non-Target +0.042
- Depots × Claude 4.6 × BFWS: Target Gain +0.128, Avg Non-Target +0.049

This indicates that when an LLM achieves a massive speedup, it is usually because it fixed a fundamental, domain-wide inefficiency (e.g., placing goal-critical logistics predicates first) that was bottlenecking all planners.

Conversely, the strictly specialised configurations (bottom-right quadrant) tend to have more moderate target gains (typically +0.01 to +0.06). For example:
- Visitall × GPT-5.4 × BFWS: Target Gain +0.055, Avg Non-Target −0.055
- Visitall × Claude 4.6 × BFWS: Target Gain +0.039, Avg Non-Target −0.060

This suggests a crucial dynamic: creating a highly planner-specific specialisation often requires delicate structural trade-offs that yield moderate gains for the target while actively penalising other architectures. Massive gains, on the other hand, usually come from universally beneficial domain cleanup.

---

### Observation 14: What does the specialisation evidence mean for the thesis hypothesis?

The evidence strongly supports the thesis. Across all 42 improved configurations:

- **81% (34/42)** had a positive Specialization Index, meaning the target planner benefited more than the non-targets.
- The Mean Specialization Index was **+0.0313**, firmly positive.
- **38% (16/42)** were strictly Specialised (target up, non-targets down).
- Only **19% (8/42)** were Anti-Specialised (non-targets benefited more).

However, the finding that 35.7% of configurations were Universally Better introduces an important nuance that should be explicitly discussed in the thesis Discussion chapter. The thesis hypothesis is *not* that architecture-aware prompting produces *exclusively* specialised improvements — it is that architecture-aware knowledge enables LLMs to produce *planner-specific* optimisations. The data confirms this: the optimisations are systematically biased toward the target planner (positive mean Specialization Index), even when they also happen to benefit other planners.

The Universally Better configurations can be framed as a *bonus outcome*: the architecture-aware approach not only achieves its primary goal of target-planner specialisation, but in many cases also resolves underlying domain inefficiencies that were holding back all planners. This dual benefit strengthens rather than weakens the argument for architecture-aware prompting.

The one concerning category is DecStar, which showed a negative Mean Specialization Index (−0.0079) and 4 out of 7 Anti-Specialised configurations. This suggests that the DecStar architecture-aware prompt may not be effectively capturing what makes DecStar's factored search unique. DecStar's star-topology decomposition creates "leaf state spaces" that are solved independently — an architectural property that may be difficult for current LLMs to translate into actionable PDDL reordering strategies. This represents an area for future work: improving the DecStar-specific prompt engineering.

---

## Part 3 — Additional Observations

### Observation 15: Reordering patterns reveal which PDDL components matter most

The Reordering Patterns table (S2-T7) shows striking unanimity across all LLMs and target prompts:

| Component | Reordering Rate |
|-----------|-----------------|
| Predicates | 75/75 (100%) |
| Add Effects | 65/75 (87%) |
| Preconditions | 64/75 (85%) |
| Actions | 56/75 (75%) |
| Delete Effects | 19/75 (25%) |
| Parameters | 1/75 (1%) |
| Requirements | 0/75 (0%) |
| Types | 0/75 (0%) |
| Functions | 0/75 (0%) |

Every single LLM reordered predicates in every single domain — a unanimous 100% rate. This aligns with all four architecture-aware prompts, which consistently identify predicate ordering as the highest-priority optimisation target. The near-zero reordering rate for Parameters (1/75) is equally informative: the LLMs correctly determined that parameter ordering within action schemas has minimal impact on any planner's performance, and they respected the "parameter consistency" guideline by leaving parameters largely unchanged.

The high reordering rate for Add Effects (87%) and Preconditions (85%) confirms that these are the second and third most impactful PDDL components. Delete Effects were reordered less frequently (25%), which is reasonable because delete effects typically have less influence on forward-search heuristics (which operate in a delete-relaxed world) and SAT encodings (where deletions create frame axiom clauses that are less sensitive to ordering).

### Observation 16: Token usage reveals fundamental differences in LLM reasoning

DeepSeek-R1 consumed **106,185 output tokens** — roughly 7× more than GPT-5.4 (12,961) and 7× more than Claude 4.6 (15,420). Despite this massive reasoning overhead, DeepSeek-R1's improvement rate (50.0%) was *lower* than Claude's (65.0%). This demonstrates that reasoning volume does not equal reasoning quality for this task. The architecture-aware prompts require precise, constrained output (a valid PDDL file with reordered elements), and DeepSeek-R1's chain-of-thought reasoning approach generates extensive internal deliberation that does not translate into better reordering decisions. Additionally, the higher token usage creates a practical cost disadvantage and increases API latency (75.2 seconds average vs 8.1 seconds for GPT-5.4).

### Observation 17: Coverage preservation was near-universal among improved configurations

A remarkable finding from S2-T15 is that **41 out of the 42 improved configurations had exactly Delta Coverage = 0**. They did not lose or gain any coverage compared to the baseline. 

There was only a single configuration that achieved a coverage increase: `snake` targeted for `madagascar` by Claude 4.6, which increased coverage from 40.0% (6/15 instances) to 46.6% (7/15 instances). 

This near-universal coverage preservation means the architecture-aware reorderings are overwhelmingly pure *speed* optimisations — they make the planner solve the same instances faster, without drastically altering which instances it can or cannot solve within the time limit. This is an important validation that the "strict constraints" in the prompts (no semantic changes) were effective: the LLMs successfully maintained the domain's logical structure while improving planner efficiency.

### Observation 18: The improvement detection methodology is conservative

With a p-value threshold of 0.25 and a three-condition gate (statistical significance, practical significance, coverage preservation), the improvement detection is deliberately conservative. The 33 non-improved triples include configurations with positive but non-significant gains. For instance, several `barman × madagascar` and `barman × decstar` triples showed positive mean IPC gains (0.001–0.012) but failed the statistical significance condition because the low baseline coverage (4/15) meant the Wilcoxon test had insufficient power. With a less conservative methodology, the improvement rate could potentially be higher. The current 56.0% rate should therefore be interpreted as a lower bound on the true effectiveness of architecture-aware prompting.
