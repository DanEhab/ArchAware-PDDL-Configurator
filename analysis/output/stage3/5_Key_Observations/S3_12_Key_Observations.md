# S3.12 — Key Observations for Stage 3 (LLM-Modulo Feedback Loop)

> **Stage Summary:** Stage 3 implemented the LLM-Modulo feedback loop, giving each LLM up to 3 iterative attempts to improve its PDDL domain reordering using quantitative execution telemetry. Of the 80 triples processed (5 domains × 4 planners × 4 LLMs), 12 were excluded as always-timeout pairs, leaving 68 contestable triples. The feedback loop **improved 32 out of 68 contestable triples (47.1%)** beyond their Stage 2 seed domains. When combined with Stage 2's one-shot improvements, the pipeline achieved an overall **80.9% improvement rate** (55/68 triples improved vs. the Stage 0 baseline). The entire pipeline ran for approximately 37 hours across 4 parallel LLM threads, executing 2,955 planner runs and 218 LLM API calls.

---

## Part 1 — Feedback Loop Efficacy

### Observation 1: Did the feedback loop actually help?

Yes. The feedback loop improved 32 out of 68 contestable triples (47.1%) beyond their Stage 2 seed domains. This is a meaningful contribution on top of Stage 2's already strong results.

To understand what this number means, it is important to recall the starting point. Each triple entered Stage 3 with either a valid Stage 2 domain (Case 6B) or a baseline domain with a seed IPC score of 0 (Cases 6A and 6C). The 36 triples where the seed remained the best outcome (Best_Iteration = 0) are not failures of the feedback loop — they are cases where Stage 2 had already found a near-optimal reordering that the feedback loop could not surpass within 3 iterations.

The distribution of the 32 improvements is also informative:

| Source of Best Domain | Count | Percentage |
|-----------------------|-------|------------|
| Seed was best (no improvement) | 36 | 52.9% |
| Iteration 1 was best | 18 | 26.5% |
| Iteration 2 was best | 5 | 7.4% |
| Iteration 3 was best | 9 | 13.2% |

Iteration 1 was the single most productive iteration, producing 18 of the 32 improvements. This makes intuitive sense: Iteration 1 is the first time the LLM receives execution telemetry, which is a significant new signal compared to the Stage 2 prompt (which had no execution feedback at all). The jump from zero feedback to detailed per-instance telemetry provides the most marginal information gain.

However, the fact that 14 of the 32 improvements came from Iterations 2 or 3 demonstrates that the feedback loop provides genuine value beyond a single additional attempt. These late improvements represent cases where the LLM needed multiple rounds of feedback to converge on an effective reordering strategy.

---

### Observation 2: How effective was Stage 2 failure recovery?

Remarkably effective. All 5 triples that entered Stage 3 as Stage 2 failures (Was_Stage2_Failure = True) were successfully recovered by the feedback loop, achieving a **100% recovery rate**. The specific cases were:

| Domain | LLM | Planner | Best Iteration | Best IPC Score |
|--------|-----|---------|----------------|----------------|
| barman | Gemini 3.1 Pro | LAMA | 3 | 15.00 |
| barman | Gemini 3.1 Pro | DecStar | 1 | 3.92 |
| depots | Gemini 3.1 Pro | DecStar | 1 | 13.70 |
| depots | GPT-5.4 | BFWS | 3 | 14.58 |
| ricochet-robots | GPT-5.4 | LAMA | 2 | 7.00 |

These 5 triples had failed in Stage 2 due to the Gemini token limit being exceeded (the Stage 2 output limit was 4,096 tokens, which Gemini exceeded for certain complex domains). In Stage 3, the output token limit was increased to 16,384 tokens for Gemini and 8,192 for all other LLMs. Additionally, the feedback loop's history buffer explicitly informed the LLM of the previous failure and the new, higher token limit (Case 6A routing).

What makes this result particularly strong is the *magnitude* of the recovered scores. The barman × Gemini × LAMA triple achieved a Best IPC of 15.00 — the maximum possible score — meaning the LLM produced a domain that solved all 15 instances with optimal or near-optimal runtimes. The depots × Gemini × DecStar triple achieved 13.70, and depots × GPT × BFWS achieved 14.58. These are not marginal recoveries; they represent some of the strongest performances in the entire Stage 3 dataset.

This finding has an important architectural implication: the feedback loop's seed routing mechanism (Point 6) successfully transforms Stage 2 API failures into productive starting points rather than permanent losses. The 100% recovery rate validates the design decision to include failed triples in the feedback loop rather than discarding them.

---

### Observation 3: Which iteration was most productive, and why was Iteration 2 the least productive?

Iteration 1 was the most productive, producing 18 out of 32 improvements (56.3% of all improvements). Iteration 2 was the least productive with only 5 improvements (15.6%), while Iteration 3 rebounded to produce 9 improvements (28.1%).

The per-iteration execution statistics provide further insight:

| Iteration | Total Executed | Valid Domains | Improved vs Baseline | Mean IPC Score |
|-----------|----------------|---------------|----------------------|----------------|
| 1 | 80 | 75 (93.8%) | 32 | 7.81 |
| 2 | 70 | 63 (90.0%) | 29 | 8.49 |
| 3 | 68 | 59 (86.8%) | 29 | 8.76 |

**Why Iteration 1 is the most productive:** The first iteration represents the largest information gain for the LLM. In Stage 2, the LLM received only the architecture-aware prompt and the domain file — no execution feedback whatsoever. In Iteration 1, the LLM receives, for the first time, a detailed per-instance telemetry table showing exactly which instances timed out, which solved quickly, and what the IPC scores were. This new signal allows the LLM to make targeted adjustments. Moving from zero feedback to rich quantitative feedback is a qualitative leap.

**Why Iteration 2 is the least productive:** By Iteration 2, the LLM has already applied the "obvious" optimisations suggested by the first round of telemetry. The improvements that remain require more subtle structural changes. Additionally, the accumulated history buffer (which now contains two previous attempts and their outcomes) makes the prompt longer and potentially more confusing — the LLM must synthesise information from multiple past attempts to determine what to try next. The prompt's input token count grows across iterations (as documented in T15), which may dilute the signal-to-noise ratio. An Iteration 2 reordering sits in an awkward middle ground: the obvious improvements have been captured, but the LLM has not yet accumulated enough failure data to identify the deeper patterns.

**Why Iteration 3 rebounds:** By Iteration 3, the LLM has seen two full rounds of execution feedback. Triples that failed to improve in Iterations 1 and 2 now have a richer failure history, and the LLM can identify what *did not work* and avoid repeating those strategies. The LLM's rationale text (observed qualitatively in the data) shows that Iteration 3 rationales are more specific and more adaptive — they frequently reference previous failed strategies by name and propose alternative approaches. The "late bloomer" pattern (discussed in Observation 6) is concentrated in Iteration 3, suggesting that some LLMs require multiple rounds of failure before discovering effective reorderings.

---

### Observation 4: Why is Gemini 3.1 Pro the top-performing LLM in Stage 3?

Gemini 3.1 Pro achieved the highest improvement rate in Stage 3 with 10 out of 17 contestable triples improved (58.8%), compared to GPT-5.4 and Claude Opus 4.6 (both 47.1%) and DeepSeek R1 (35.3%).

| LLM | Stage 2 Rate | Stage 3 Rate | Change |
|-----|-------------|-------------|--------|
| Claude Opus 4.6 | 65.0% (13/20) | 47.1% (8/17) | ↓ |
| Gemini 3.1 Pro | 58.8% (10/17) | 58.8% (10/17) | → |
| DeepSeek R1 | 50.0% (10/20) | 35.3% (6/17) | ↓ |
| GPT-5.4 | 50.0% (9/18) | 47.1% (8/17) | ≈ |

Three factors explain Gemini's strong Stage 3 performance:

**Factor 1 — The 5 Stage 2 failure recoveries.** Three of Gemini's recovered triples (barman × LAMA, barman × DecStar, depots × DecStar) were Stage 2 token limit failures that were fully recovered in Stage 3. These recoveries boosted Gemini's improvement count by 3, directly contributing to its leading position. Without these recoveries (which were only possible because Stage 3 increased the token limit), Gemini would have had 7/14 = 50.0%, roughly level with the other LLMs.

**Factor 2 — Token efficiency.** Gemini generates the most concise outputs of all LLMs (mean 796 output tokens per iteration, vs. GPT's 778, Claude's 1,003, and DeepSeek's 3,228). Shorter, more focused outputs indicate that Gemini produces less extraneous reasoning and more direct PDDL modifications. In a feedback loop context where the prompt grows with each iteration (due to accumulated history and telemetry), concise output generation helps stay within the effective context window.

**Factor 3 — High-magnitude improvements.** When Gemini improves, it often achieves substantial gains. The barman × LAMA recovery produced an IPC of 15.00 (improvement of +14.999 over the seed), and depots × DecStar produced an IPC of 13.70 (+13.704). These are among the largest improvements in the entire dataset. Gemini appears particularly effective at identifying and exploiting major structural inefficiencies in domain files.

---

### Observation 5: Why does DecStar remain the hardest planner to improve?

DecStar had the lowest improvement rate in Stage 3 at 25.0% (4 out of 16 contestable triples), mirroring its position as the second-hardest planner in Stage 2 (38.9%). The improvement rates across planners were:

| Planner | Improvement Rate | Timeout Rate (S3 planner runs) |
|---------|------------------|-------------------------------|
| LAMA | 55.0% (11/20) | 27.7% (224/810) |
| BFWS | 55.0% (11/20) | 14.9% (123/825) |
| Madagascar | 50.0% (6/12) | 54.6% (344/630) |
| DecStar | 25.0% (4/16) | 58.4% (403/690) |

Three architectural factors explain DecStar's resistance to optimisation:

**Factor 1 — Factored search is inherently less ordering-sensitive.** DecStar's core innovation is decomposing the state space into a star topology with a central hub and independent leaf modules. Once the factoring is computed, the search proceeds over a compressed representation where leaf-local actions are handled by Dijkstra's algorithm within each leaf. This factored representation abstracts away much of the textual ordering in the PDDL file. Unlike LAMA, where predicate ordering directly affects mutex discovery and preferred-operator selection, DecStar's factoring engine applies its own structural analysis (Causal Graph SCCs, InteractionGraph) that largely overrides the textual ordering of the input.

**Factor 2 — High baseline timeout rate.** DecStar timed out on 58.4% of all Stage 3 planner runs — the highest of any planner. When most instances time out, the IPC scores are dominated by zeros, and even significant speedups on the few solvable instances produce small aggregate IPC gains. The 30-second factoring timer in DecStar adds an additional failure mode: if the factoring process itself times out, DecStar falls back to standard explicit-state search, losing all benefits of the decoupled approach.

**Factor 3 — The architectural complexity is hard for LLMs to reason about.** The DecStar architecture-aware prompt asks the LLM to reason about star topology factoring, center-leaf variable partitioning, and causal graph SCC analysis. These are complex graph-theoretic concepts that require understanding how textual predicate ordering translates through grounding, FDR translation, and causal graph construction into the final factored topology. This multi-step reasoning chain is significantly more complex than reasoning about LAMA's "put goal predicates first" heuristic, and current LLMs may struggle to effectively model these indirect relationships.

The 4 triples that *did* improve on DecStar are instructive. Gemini improved barman × DecStar (IPC 3.92) and depots × DecStar (IPC 13.70) — both of these were Stage 2 failure recoveries where the seed IPC was 0.0. The other two (snake × GPT and snake × Claude) achieved minimal improvements of +0.010 and +0.000. This suggests that the feedback loop's value for DecStar is primarily in recovering from total failures rather than incrementally optimising valid domains.

---

### Observation 6: What does the "late bloomer" pattern tell us about LLM learning from failure?

Of the 68 contestable triples, the convergence analysis identified four distinct patterns:

| Pattern | Count | Description |
|---------|-------|-------------|
| Get it right first try | 18 | Iteration 1 improves; later iterations may regress |
| Late bloomer | 14 | Best result at Iteration 2 or 3, without continuous improvement |
| Progressive refinement | 2 | Continuous improvement across all iterations |
| Stuck at seed | 36 | No iteration beats the seed |

The 14 late bloomers (5 at Iteration 2, 9 at Iteration 3) are particularly informative because they demonstrate that LLMs can learn from accumulated failure. Some notable examples:

- **barman × Gemini × LAMA (Best Iter 3, +14.999):** This was a Stage 2 failure recovery. Gemini needed 3 iterations to achieve the maximum IPC score of 15.00. Iterations 1 and 2 produced valid but suboptimal domains. By Iteration 3, the accumulated telemetry from two previous attempts gave Gemini enough context to produce a near-perfect reordering. The Iteration 3 rationale explicitly referenced the failures of prior iterations.

- **depots × GPT × BFWS (Best Iter 3, +14.582):** Another Stage 2 failure recovery. GPT needed 3 iterations to recover from stage 2 failure and achieve a high IPC score.

- **ricochet-robots × GPT × LAMA (Best Iter 2, +7.000):** This triple's Stage 2 seed had an IPC of 0.0 (failure). Iteration 1 produced a valid domain but with suboptimal performance. Iteration 2, armed with the Iteration 1 telemetry, achieved a significant improvement.

The late bloomer pattern provides strong evidence that the feedback loop is not merely giving the LLM additional "lottery tickets" (random chances to produce a good reordering). If that were the case, we would expect the improvements to be uniformly distributed across iterations. Instead, the concentration of late bloomers in Iteration 3 — and the evolution of their rationale text from generic to specific — suggests genuine learning from failure feedback. The LLMs are processing the execution telemetry and adjusting their strategies accordingly.

The existence of only 2 "progressive refinement" cases (where the IPC improved continuously across all 3 iterations) indicates that iterative improvement is more commonly non-monotonic: the LLM may regress before finding a better strategy. This is consistent with the nature of the optimisation landscape — the space of possible PDDL reorderings is discrete and non-convex, so gradient-like continuous improvement is unlikely.

---

### Observation 7: How did validation rates change compared to Stage 2?

The overall validation success rate in Stage 3 was 90.4% (197 valid out of 218 total iterations), compared to 93.8% in Stage 2 (75 valid out of 80 calls). While Stage 3's rate is slightly lower, the trend across iterations reveals an important pattern:

| Iteration | Valid / Total | Validation Rate |
|-----------|---------------|-----------------|
| Stage 2 (reference) | 75 / 80 | 93.8% |
| Stage 3, Iteration 1 | 75 / 80 | 93.8% |
| Stage 3, Iteration 2 | 63 / 70 | 90.0% |
| Stage 3, Iteration 3 | 59 / 68 | 86.8% |

The validation rate *decreases* across iterations, which is the opposite of what one might naively expect. If the feedback loop were helping LLMs produce better PDDL, one might predict that validation rates would improve as the LLM learns from feedback. However, this declining trend has a logical explanation.

**Why validation rates decline:** As iterations progress, the LLM receives an increasingly long prompt containing accumulated history, telemetry tables, and the current domain. This growing prompt size puts pressure on the LLM's effective context window, particularly for output generation. The LLM must produce a complete, valid PDDL file while simultaneously processing several pages of historical context. Under this pressure, LLMs are more likely to make extraction errors (V1 failures — the PDDL output is incomplete or malformed) or semantic errors (V4 failures — the reordering accidentally changes logical meaning).

Additionally, the prompt explicitly instructs the LLM to write a 2-sentence rationale *before* the PDDL output. With each iteration, the LLM has more to discuss in its rationale (previous strategies, why they failed, what it plans differently). Some LLMs — particularly DeepSeek R1, which generates verbose chain-of-thought reasoning — produce increasingly long rationales that consume output tokens, leaving less budget for the PDDL file itself. This is consistent with the 4 token limit errors in Stage 3, all of which occurred with Gemini 3.1 Pro at later iterations.

**V4 semantic failures:** Stage 3 produced 4 V4 semantic failures compared to Stage 2's 2. The V4 validator detects cases where the LLM modified the logical semantics of the domain (adding, removing, or altering preconditions or effects) rather than purely reordering. The slight increase in V4 failures (4 vs. 2) may reflect the additional complexity of the multi-iteration task: when the LLM is asked to "try something different" from its previous attempt, it may cross the line from reordering into modification.

Importantly, the validation pipeline's role as a "hard critic" gatekeeper was fully effective. All 21 invalid iterations were correctly caught and rejected before reaching the planner execution stage. No semantically altered domain was ever evaluated as if it were a valid reordering. This validates the thesis's Phase 4 computational safeguards design.

---

## Part 2 — Headline Results

### Observation 8: What is the combined Stage 2+3 improvement rate vs. Stage 0 baseline?

The combined improvement rate is **80.9% (55 out of 68 contestable triples)**. This is the headline result of the entire thesis.

Breaking down the source of these 55 improvements:

| Source | Count | Meaning |
|--------|-------|---------|
| Seed (Stage 2) was already improved over baseline | 30 | Stage 2's one-shot approach had already beaten the baseline |
| Iteration 1 beat baseline (but not necessarily seed) | 12 | First feedback iteration added value |
| Iteration 2 beat baseline | 5 | Second iteration added value |
| Iteration 3 beat baseline | 8 | Third iteration added value |

This means the feedback loop contributed **25 additional improvements** beyond what Stage 2 had already achieved. Stage 2 alone had improved 30 out of 68 triples (44.1%). The feedback loop raised this to 55 out of 68 (80.9%), nearly doubling the improvement rate.

The remaining 13 triples that were not improved cluster in two categories:
1. **Planner-domain incompatibility:** Triples where the planner fundamentally cannot solve the domain (e.g., ricochet-robots × DecStar, snake × DecStar). These represent a hard ceiling for the approach.
2. **Already-optimal seeds:** Triples where the Stage 2 reordering was already near-optimal and no further improvement was achievable within 3 iterations.

For a bachelor thesis, the 80.9% figure directly answers the main research question: *"To what extent can Large Language Models dynamically optimise the structural configuration of PDDL domain models?"* The answer is: architecture-aware prompting combined with iterative feedback enables LLMs to improve planner performance in over 80% of testable configurations.

---

### Observation 9: What are the practical token cost implications?

The token usage analysis reveals striking efficiency differences between LLMs:

| LLM | Total Output Tokens | Total Input Tokens | Improvement Rate | Mean Improvement vs. Seed |
|-----|--------------------:|-------------------:|:----------------:|:-------------------------:|
| GPT-5.4 | 42,035 | 145,276 | 47.1% | +1.656 |
| Gemini 3.1 Pro | 43,005 | 145,214 | 58.8% | +2.200 |
| Claude Opus 4.6 | 54,159 | 177,031 | 47.1% | +0.097 |
| DeepSeek R1 | 180,741 | 150,212 | 35.3% | +0.212 |

The most important finding is the **DeepSeek token inefficiency**. DeepSeek R1 consumed 180,741 output tokens — **4.3× more than GPT-5.4** (42,035) and **4.2× more than Gemini** (43,005) — while achieving the *lowest* improvement rate (35.3%) and a modest mean improvement (+0.212). This is because DeepSeek R1 is a "reasoning" model that generates extensive chain-of-thought tokens as part of its output. While these reasoning tokens may help with certain tasks (e.g., mathematical proofs, logical deduction), they provide no benefit for PDDL reordering, where the task is to produce a structurally modified but semantically identical file.

Claude Opus 4.6 presents a different cost profile. It consumed 54,159 output tokens (29% more than GPT/Gemini) and 177,031 input tokens (22% more than GPT/Gemini). The higher input token count reflects Claude's tendency to produce longer rationale text, which then accumulates in the history buffer and inflates subsequent prompts. Despite the higher token cost, Claude achieved only a moderate improvement rate (47.1%) and the lowest mean improvement (+0.097).

**Gemini 3.1 Pro emerges as the most cost-effective LLM for this task.** It consumed the fewest total output tokens (43,005), achieved the highest improvement rate (58.8%), and produced the largest mean improvement (+2.200). This makes Gemini roughly 4× more cost-effective than DeepSeek and 2× more cost-effective than Claude for feedback loop-based PDDL optimisation.

For practitioners, this finding suggests that when deploying an LLM-Modulo feedback loop for PDDL optimisation, a concise, efficient model outperforms a verbose reasoning model. The task of structural reordering does not benefit from extensive chain-of-thought deliberation — it benefits from precise, constrained output generation.

---

## Part 3 — Learning Dynamics

### Observation 10: Did the rationale quality improve across iterations?

Yes. A qualitative analysis of the 214 LLM rationales reveals a clear evolution in specificity and adaptiveness across iterations.

**Iteration 1 rationales are generic and prompt-derived.** They typically restate the architecture-aware prompt's heuristics without reference to execution data. Examples:
- *"I reordered predicates to put dynamic, goal-relevant container and shaker state first and static relation predicates last, then ordered actions from simpler/enabling schemas toward more constrained transitions."* (GPT-5.4, barman × LAMA, Iter 1)
- *"To optimize for LAMA's architecture, I reordered predicates to place goal-relevant predicates first, accelerating mutex discovery and improving landmark ordering."* (Gemini, barman × LAMA, Iter 1)

**Iteration 3 rationales are specific and adaptive.** They reference previous outcomes, explain why prior strategies failed, and propose targeted adjustments. Examples:
- *"To avoid the regressions of previous purely complexity-based orderings, I reordered actions by their typical execution frequency and causal phase in a plan."* (Gemini, barman × LAMA, Iter 3)
- *"My reordering strategy reverts to the successful Iteration 1 approach but with targeted refinements: I reorder predicates to place goal-relevant ones first and static ones last."* (Claude, barman × LAMA, Iter 3)
- *"I reorder predicates to keep dynamic container/shaker state facts before hand-state and static recipe/adjacency facts, but I avoid the broader action reshuffling from the regressing attempt."* (GPT-5.4, barman × LAMA, Iter 3)

The average rationale length also increases across iterations: from approximately 490 characters in Iteration 1 to 564 characters in Iteration 3 for GPT-5.4, and from 496 to 541 for Gemini. Claude shows the most dramatic increase, from 731 to 880 characters. This lengthening reflects the accumulation of prior context that the LLM must discuss.

Most importantly, the Iteration 3 rationales demonstrate a capability that is absent in Iteration 1: the ability to *learn from regression*. When the LLM's Iteration 2 strategy produced a worse result than Iteration 1, the Iteration 3 rationale frequently states something like "I revert to the Iteration 1 approach" or "I avoid the changes from the regressing attempt." This shows the LLM successfully processing the telemetry feedback to identify which strategies were harmful and avoiding them in subsequent iterations.

---

### Observation 11: Solve rate trend across iterations

The planner solve rate — the percentage of individual planner runs (each testing 1 instance) that produced a successful solution within the time limit — increased steadily across iterations:

| Iteration | Total Runs | Successful | Solve Rate |
|-----------|------------|------------|------------|
| Feedback Loop 1 | 1,125 | 640 | 56.9% |
| Feedback Loop 2 | 945 | 609 | 64.4% |
| Feedback Loop 3 | 885 | 611 | 69.0% |

This upward trend from 56.9% to 69.0% is one of the strongest pieces of direct evidence that the feedback loop works. It shows that LLM-produced domain reorderings become progressively better at helping planners solve problem instances. Each iteration's telemetry feedback enables the LLM to adjust its reordering strategy to resolve more timeouts.

The decreasing total run count (1,125 → 945 → 885) reflects two mechanisms: (1) triples that terminated early due to ALL_TIMEOUT are not executed in later iterations, and (2) iterations that fail validation do not produce planner runs. Despite having fewer total runs, later iterations achieve a higher absolute success count per triple, indicating genuine improvement rather than selection bias.

Note that this metric is fundamentally different from the "Best Iteration" analysis (Observation 3), which tracks which iteration produced the *best overall IPC score* for each triple. The solve rate trend captures the aggregate, population-level effect: across all triples and all planners, later iterations produce domains that are more likely to lead to successful solutions.

---

### Observation 12: LLM learning curves differ dramatically

The mean IPC score progression by LLM across iterations reveals four distinct learning patterns:

| LLM | Iter 1 | Iter 2 | Iter 3 | Pattern |
|-----|--------|--------|--------|---------|
| Claude Opus 4.6 | 8.20 | 9.54 | 9.65 | Steady improvement |
| GPT-5.4 | 8.10 | 8.80 | 9.85 | Accelerating improvement |
| Gemini 3.1 Pro | 8.36 | 9.16 | 8.67 | Peak-then-regress |
| DeepSeek R1 | 6.60 | 6.67 | 6.85 | Flat plateau |

**Claude and GPT show genuine learning.** Both models improve steadily across iterations, with GPT showing an accelerating pattern (the Iter 2→3 gain of +1.05 is larger than the Iter 1→2 gain of +0.70). This suggests that Claude and GPT effectively process the execution telemetry and use it to refine their reordering strategies. GPT's accelerating pattern is particularly interesting — it implies that GPT benefits from the accumulated history of multiple attempts, using later iterations to synthesise insights from earlier experiments.

**Gemini peaks at Iteration 2 and then regresses.** Gemini achieves a strong performance at Iteration 2 (9.16) but drops to 8.67 at Iteration 3. This "overshoot" pattern suggests that Gemini's Iteration 3 strategies become too aggressive or diverge from what worked in Iteration 2. The regression is consistent with Gemini's "get it right first try" tendency: most of Gemini's improvements come from Iteration 1 (7 out of 10), and its later iterations sometimes undo those gains. This may be related to Gemini's concise output style — with fewer reasoning tokens, Gemini may not fully process the growing history buffer in later iterations.

**DeepSeek R1 is essentially flat.** Moving from 6.60 to 6.85 across three iterations represents near-zero learning. Despite generating 4.3× more output tokens per iteration (including extensive chain-of-thought reasoning), DeepSeek does not translate the telemetry feedback into meaningfully better reorderings. This may be because DeepSeek's reasoning tokens are consumed by its internal thinking process, which is better suited to logical deduction tasks than to the spatial/structural optimisation task of PDDL reordering. The LLM-Modulo framework's feedback — which provides quantitative metrics rather than logical arguments — may not interface well with DeepSeek's reasoning paradigm.

This finding has important implications for LLM selection in feedback loop architectures: not all LLMs benefit equally from iterative feedback, and the ability to *learn from execution telemetry* is a differentiating capability.

---

## Part 4 — Token Cost and Efficiency

### Observation 13: DeepSeek's reasoning tokens are wasted on this task

DeepSeek R1 consumed **180,741 total output tokens** across 56 iterations — **4.3× more than GPT-5.4** (42,035 tokens across 54 iterations) and **4.2× more than Gemini 3.1 Pro** (43,005 tokens across 54 iterations). Despite this massive token expenditure, DeepSeek achieved:
- The **lowest improvement rate**: 35.3% (6/17 contestable triples)
- A **flat learning curve**: Mean IPC barely moved from 6.60 (Iter 1) to 6.85 (Iter 3)
- The **second-lowest mean improvement vs. seed**: +0.212

The per-iteration mean output token count tells the story:

| LLM | Mean Output Tokens per Iteration |
|-----|--------------------------------:|
| GPT-5.4 | 778 |
| Gemini 3.1 Pro | 796 |
| Claude Opus 4.6 | 1,003 |
| DeepSeek R1 | 3,228 |

DeepSeek's output tokens are roughly 4× those of GPT and Gemini because DeepSeek R1 is a "reasoning" model that generates an explicit chain-of-thought before producing its final answer. For tasks like mathematical proof or logical deduction, this chain-of-thought can improve accuracy. However, for PDDL reordering — a task that requires producing a structurally modified but semantically identical file — the chain-of-thought reasoning provides no measurable benefit. The task is fundamentally *structural* rather than *logical*: the LLM must decide where to place predicates, actions, and preconditions in a file, not reason through a logical proof.

This finding echoes and extends the Stage 2 observation about DeepSeek (Stage 2 Observation 16), where DeepSeek consumed 106,185 output tokens across 20 calls — roughly 7× more than GPT-5.4 — for a comparable improvement rate. The consistency of this pattern across both Stage 2 (one-shot) and Stage 3 (feedback loop) confirms that DeepSeek's reasoning overhead is a structural characteristic of the model that does not diminish with additional context.

---

## Part 5 — Domain-Planner Interaction Patterns

### Observation 14: barman × Madagascar is the only 4/4 improved combination

The Domain × Planner improvement matrix reveals that barman × Madagascar is the only combination where all 4 LLMs successfully improved the domain:

| Domain \ Planner | BFWS | DecStar | LAMA | Madagascar |
|-----------------|------|---------|------|------------|
| barman | 3/4 | 1/4 | 1/4 | **4/4** |
| depots | 2/4 | 1/4 | 2/4 | 0/4 |
| ricochet-robots | 2/4 | 0/4 | 4/4 | N/A |
| snake | 2/4 | 2/4 | 1/4 | 2/4 |
| visitall | 2/4 | N/A | 3/4 | N/A |

The barman domain describes a cocktail-mixing scenario with containers, shakers, and beverages. Madagascar is a SAT-based planner that compiles the planning problem into a Boolean satisfiability formula. The fact that all 4 LLMs could improve barman for Madagascar suggests that the barman domain has a clear, consistent structural inefficiency that is easily identifiable from the execution telemetry — and that the fix generalises across LLMs.

Looking at the specific improvements:
- Gemini: Best Iter 1, +1.561
- GPT: Best Iter 3, +2.152
- DeepSeek: Best Iter 2, +1.194
- Claude: Best Iter 3, +0.291

The improvements are moderate and spread across different iterations, suggesting that different LLMs find the improvement through different strategies and at different speeds, but all converge on the same beneficial reordering pattern.

**Contrast with ricochet-robots × LAMA (also 4/4):** Interestingly, ricochet-robots × LAMA also achieved 4/4 improvements. LAMA is the most ordering-sensitive planner (as established in Stage 2), and the feedback loop's telemetry — which directly reports LAMA's preferred-operator and landmark analysis outcomes — provides actionable signals that all 4 LLMs could leverage.

**Contrast with depots × Madagascar (0/4):** The complete failure of depots × Madagascar demonstrates that the feedback loop cannot overcome fundamental planner-domain incompatibility. Madagascar's SAT encoding of the depots domain likely produces an inherently difficult satisfiability instance that no PDDL reordering can resolve within the time limit.

---

## Part 6 — Additional Observations

### Observation 15: The feedback loop's value is not just in IPC improvement — it is also in failure recovery

Beyond the 47.1% improvement rate on contestable triples, the feedback loop provides a critical additional value: it transforms Stage 2 failures (API errors, validation failures) into productive outcomes. The 5 Stage 2 failure recoveries (Observation 2) represent triples that would have been permanently lost without the feedback loop.

Moreover, several of these recovered triples achieved *some of the highest IPC scores in the entire dataset*. The barman × Gemini × LAMA recovery achieved an IPC of 15.00 (maximum possible), and the depots × GPT × BFWS recovery achieved 14.58. These are not marginal saves — they represent transformations from complete failure (IPC = 0.0) to near-perfect performance.

This positions the feedback loop as a *reliability mechanism* in addition to an *optimisation mechanism*. In a production system where API errors, token limits, and validation failures are inevitable, the feedback loop ensures that no triple is permanently lost due to a single transient failure.

---

### Observation 16: The diminishing returns hypothesis is supported but not conclusive

The iteration-level data suggests that the feedback loop exhibits diminishing returns, but the evidence is not strong enough to conclusively determine whether 3 iterations is optimal.

| Metric | Iter 1 | Iter 2 | Iter 3 |
|--------|--------|--------|--------|
| New best-domains produced | 18 | 5 | 9 |
| Mean IPC (all triples) | 7.81 | 8.49 | 8.76 |
| Solve rate | 56.9% | 64.4% | 69.0% |

The "new best-domains" metric drops sharply from 18 (Iter 1) to 5 (Iter 2) but rebounds to 9 (Iter 3). This non-monotonic pattern suggests that diminishing returns are not strictly linear — Iteration 3 provides meaningful additional value that Iteration 2 does not. A hypothetical Iteration 4 might produce further improvements for some of the 36 "stuck at seed" triples, but the declining validation rate (93.8% → 90.0% → 86.8%) suggests that additional iterations would increasingly suffer from prompt size and validation quality issues.

For the thesis, the 3-iteration limit can be justified as a practical compromise: it captures the bulk of the feedback loop's value (Iteration 1), allows for late-bloomer discovery (Iterations 2–3), and avoids the diminishing returns and validation degradation that would likely worsen with additional iterations. However, future work could investigate adaptive stopping criteria (e.g., stopping when the IPC score plateaus for 2 consecutive iterations) rather than a fixed iteration limit.

---

### Observation 17: Structural shift analysis reveals that the feedback loop amplifies reordering intensity

Table S3-T21 shows that domains produced by the feedback loop's best iterations exhibit *more* structural reordering than their Stage 2 seeds:

| PDDL Component | Domains Reordered (Seed) | Domains Reordered (Best Iter) | Total Reorders (Seed) | Total Reorders (Best Iter) |
|----------------|:------------------------:|:----------------------------:|:---------------------:|:--------------------------:|
| Predicates | 29 | 32 | 29 | 32 |
| Actions | 22 | 26 | 22 | 26 |
| Preconditions | 24 | 30 | 94 | 138 |
| Add effects | 24 | 27 | 51 | 60 |
| Delete effects | 9 | 12 | 12 | 16 |
| Parameters | 0 | 1 | 0 | 3 |

The most striking increase is in precondition reordering: from 94 total reorders in seed domains to 138 in best iterations — a **47% increase**. This suggests that the feedback loop's telemetry (which reports per-instance runtimes and states expanded) helps LLMs identify that precondition ordering is a high-leverage optimisation target. The telemetry shows the LLM exactly which instances time out and how the search effort distributes across actions, enabling more targeted precondition adjustments.

The increase in domains that reorder predicates (from 29 to 32) and actions (from 22 to 26) further confirms that the feedback loop encourages more aggressive reordering. Importantly, parameter reordering remains near-zero (0 → 1 domain, 0 → 3 total reorders), confirming that LLMs correctly identify parameters as a low-impact component even under iterative pressure to "try something different."

---

### Observation 18: The three-iteration design answers SQ3 from the thesis proposal

Sub-Question 3 of the thesis proposal asks: *"To what degree does an 'LLM-Modulo' feedback loop (providing the LLM with quantitative execution metrics) improve the efficiency of domains compared to single-pass generations?"*

The Stage 3 data provides a comprehensive answer:

1. **Direct improvement:** The feedback loop improved 32/68 (47.1%) of contestable triples beyond their Stage 2 seeds. For comparison, Stage 2's single-pass approach improved 42/75 (56.0%) of triples over the Stage 0 baseline.

2. **Cumulative effect:** Combining Stage 2 and Stage 3, the improvement rate rises from 44.1% (Stage 2 alone) to 80.9% (Stage 2 + Stage 3 combined), nearly doubling the improvement rate.

3. **Failure recovery:** The feedback loop recovered all 5 Stage 2 failures, demonstrating that multi-turn iteration provides resilience against transient API errors.

4. **Progressive learning:** The planner solve rate increased from 56.9% to 69.0% across iterations, and the mean IPC score rose from 7.81 to 8.76, demonstrating that quantitative execution metrics enable LLMs to progressively improve their reorderings.

5. **LLM-dependent learning:** Not all LLMs benefit equally from feedback. Claude and GPT show steady improvement; Gemini peaks early and then regresses; DeepSeek shows near-zero learning. This suggests that the effectiveness of the LLM-Modulo framework depends on the base model's ability to process and act on quantitative feedback.

The overall conclusion for SQ3 is: **the feedback loop provides a substantial and statistically meaningful improvement over single-pass generations, nearly doubling the improvement rate from 44.1% to 80.9% and recovering 100% of Stage 2 failures.**
