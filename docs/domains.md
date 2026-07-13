# 🗺️ The Five Benchmark Domains

Five IPC benchmark domains were selected to span the full structural spectrum — from a near‑minimal single‑action domain to a densely typed, high‑arity one — across more than two decades of competition history. Each links to its folder in this repository, where you'll find the reference `domain.pddl`, all 20 problem instances, and the 15 selected (seed‑42) instances used in every experiment.

| Domain | IPC Year | Structural niche | In this repo |
|---|:--:|---|---|
| **VisitAll** | 2014 | Minimal baseline — pure graph reachability (1 action, 3 predicates) | [`benchmarks/visitall/`](../benchmarks/visitall/) |
| **Snake** | 2018 | Untyped, negative preconditions, irreversible dead‑end states | [`benchmarks/snake/`](../benchmarks/snake/) |
| **Ricochet Robots** | 2023 | Modern mid‑range; the only domain using `:action-costs` and numeric fluents | [`benchmarks/ricochet-robots/`](../benchmarks/ricochet-robots/) |
| **Depots** | 2002 | Typed logistics; 3‑level type hierarchy; spatially decoupled sub‑problems | [`benchmarks/depots/`](../benchmarks/depots/) |
| **Barman** | 2014 | Maximal complexity anchor — highest action count (12) and arity (6) | [`benchmarks/barman/`](../benchmarks/barman/) |

Each domain folder is organised identically:

```
benchmarks/<domain>/
├── domain.pddl        # the reference domain model
├── all_instances/     # all 20 problem instances (instance-01 … instance-20)
└── instances/         # the 15 selected instances used in every stage
```

---
← Back to the [README](../README.md)
