# Hox: Scoped, Recursive Session Projections over Propagator Networks

> *"An analogy for the Hox genes can be made to the role of a play director who calls which scene the actors should carry out next. If the play director calls the scenes in the wrong order, the overall play will be presented in the wrong order."*

**Hox** is an experimental architectural prototype written in **pure functional Python 3.14**:
1. **Multiparty Session Types (MPST / Choreographies)**: Choice-guarded recursion ($\mu t$) with scoped projection that prunes non-participating roles.
2. **Sussman Propagator Networks**: Monotonic spatial constraints (`separation_constraint`, `pin_constraint`) with structured result types (`SolveSuccess | SolveInconsistent | SolveStepLimit`).
3. **The Hox Bridge**: Enforces the **"Curtains Closed" Privacy Rule** via projected footprint views (`project_tissue`), ensuring decision predicates physically cannot snoop on foreign cells.

---

## Architectural Mechanisms

```
                     Choice-Guarded Recursive Protocol
                   μ(Negotiate) . choice by Sidebar {
                       Retry:  Sidebar -> Main : CounterOffer . Negotiate,
                       Commit: Sidebar -> Main : Accept . end
                   }
                                  │
                       Scoped project(global, role)
                      (Prunes non-participating roles)
                                  ▼
                    Projected Local Endpoints (CFSMs)
                    • Per-role isolated recursion environments
                                  │
                                  ▼
                    Privacy Footprint View (No Snooping)
                     project_tissue(tissue, footprint)
                                  │
                                  ▼
                     Monotonic Spatial Propagation
                     • separation_constraint (bump right)
                     • pin_constraint (zero drift)
                                  │
                                  ▼
                      Structured SolveResult
                SolveSuccess | SolveInconsistent | SolveStepLimit
```

---

## Potential Applications

| Domain | How the Architecture Applies | Trade-offs & Fit |
| :--- | :--- | :--- |
| **Interactive & Infinite Canvases** | Generates proposed reflows (e.g. cards displacing neighbors, containers resizing to content) from drag/resize gestures. Emits clean batch data (`LayoutPlan`) on pointer release. | **Good Fit**: Solves overlap management locally without global solver lag. |
| **Multi-Disciplinary CAD & Spatial Design** | Resolves local clearances and physical calculations within subsystems, while phased project handoffs follow a verified coordination protocol. | **Natural Fit**: Matches how structural and MEP engineering handoffs work. |
| **Multi-Agent Systems** | Protocol layer coordinates agent turn-taking and message schemas; monotonic constraint network acts as a shared factual blackboard. | **Plausible Fit**: Prevents conversation loops and fact retraction. |

---

### Conceptual Influences

The architecture draws on three distinct threads in systems design:
* **Christopher Alexander (Generative Sequences)**: Separating the sequential, step-by-step unfolding of a structure (the order of decisions) from the local adaptation to spatial forces (geometry and clearances). The choreography represents the unfolding sequence; the propagators resolve local forces.
* **Gerald Sussman & Alexey Radul (Propagators)**: Using autonomous, multi-directional constraint networks that settle to a fixed point through local monotonic accumulation, avoiding a central master equation.
* **Alan Kay (Biological Scaling)**: Using a small set of selector directives (Hox genes) to parameterize a large collection of decentralized, locally communicating entities.

---

### Pragmatic Boundaries

* **Good Use Cases**:
  - Local interaction loops on an infinite canvas where cards need spatial rules (elastic displacement, container padding, zero-drift pins).
  - Systems where continuous preview relaxation must remain cleanly decoupled from durable, single-batch document writes (CRDTs).
  - Multi-party state transitions that need deadlock-free guarantees without manual lock management.
* **Bad Use Cases / Anti-Patterns**:
  - Mundane web CRUD applications where standard request-response pipelines are already well-understood.
  - Distributed network locking (running MPST across peers over WebSockets breaks the offline-first, conflict-free guarantees of CRDTs).

---

## Directory Structure

```
hox/
├── propagator/
│   ├── lattice.py          # Pure interval semilattice [lo, hi], merge, plus, minus
│   ├── propagators.py      # sum_constraint, separation_constraint, pin_constraint
│   └── engine.py           # Fixed-point solver returning SolveResult
├── session/
│   ├── types.py            # ADTs with recursion: RecG, VarG, RecL, VarL, ChoiceG, SendG...
│   ├── projection.py       # Scoped projection with non-participating role pruning
│   └── runtime.py          # Per-role unrolling and state transition functions
├── bridge/
│   └── functional_bridge.py# project_tissue (footprint views) & decide_branch
└── demo.py                 # Multi-round negotiation & 3-card bump demo
```

---

## Running the Demo

```bash
python3 -m hox.demo
```

### What You Will See:
1. **Desktop Viewport (720px)**: Sidebar asks for Full Mode $[200, 300]\text{px}$. Fits on Round 1 and commits to 250px.
2. **Tablet Viewport (520px)**: Sidebar asks for Full Mode. Contradiction detected (`SolveInconsistent`). Sidebar chooses `Retry` and counter-offers Compact Mode $[80, 150]\text{px}$. Fits on Round 2 and commits to 120px!
3. **3-Card Spatial Bump**: Card A bumps Card B from 150px to 220px. Card C (pinned at 600px) has **zero drift** ($[600, 600]$).

---

## Running the Test Suite

```bash
python3 -m unittest discover -s tests
```
*17 tests passing in ~0.001s*, verifying semilattice arithmetic, confluence under merge (CRDT-readiness), scoped recursive projection, structured failure modes, zero-drift spatial pinning, and footprint privacy.
