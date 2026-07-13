# 🐳 The Four Planners

This project deliberately selects four planners that solve PDDL problems through **fundamentally different** search paradigms — so that the effect of architecture‑aware reordering can be measured across genuinely distinct engines. Each planner runs in its own Docker container; the build files live under [`planners/`](../planners/).

| Planner | Search Paradigm | Notable | Source / Reference |
|---|---|---|---|
| **LAMA‑first** (Fast Downward) | Heuristic forward search (FF heuristic + landmarks) | Gold‑standard satisficing baseline; official IPC 2023 Agile baseline | [fast-downward.org](https://www.fast-downward.org/) · [github.com/aibasel/downward](https://github.com/aibasel/downward) |
| **LAPKT‑BFWS‑Preference** | Width‑based search (novelty) | Winner, IPC 2018 Agile track; explores structurally *novel* states instead of goal‑distance estimates | [nirlipo/BFWS-public](https://github.com/nirlipo/BFWS-public) · [LAPKT toolkit](https://github.com/LAPKT-dev/LAPKT-public) |
| **DecStar** | Decoupled search (star topology) | Winner, IPC 2023 Agile track; extends Fast Downward by factoring the task into a center + independent leaves | [Planning.Wiki](https://planning.wiki/ref/planners/decstar) · [Daniel Gnad](https://dgnad.github.io/) · [IPC 2023 abstract (PDF)](https://ipc2023-classical.github.io/abstracts/planner15_decstar.pdf) |
| **Madagascar** (MpC) | SAT‑based planning | Compiles the task into Boolean formulae (one per plan length) and delegates them to a SAT solver | [research.ics.aalto.fi/software/sat/madagascar](https://research.ics.aalto.fi/software/sat/madagascar/) |

### Why these four?
They were chosen from an initial pool of 35 classical planners via a four‑step filter (agile & non‑portfolio → proven track record → open‑source & Dockerisable → **distinct architectures**). The last filter is the important one: most top‑ranked IPC planners are variants of Fast Downward, so simply picking "the top four" would test one architecture four times. Instead, each engine here reads and searches a domain in a fundamentally different way — heuristic forward search, novelty/width search, decoupled star‑topology search, and SAT compilation.

Each planner's container is built from [`planners/<name>/Dockerfile`](../planners/) with a small `planner_exec` wrapper that runs the engine under a 360 s / 8 GB / 1‑CPU budget and emits standardised `[RESULT]` / `[METRIC]` lines.

---
← Back to the [README](../README.md)
