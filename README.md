# Hox: Scoped, Recursive Session Projections over Propagator Networks

> *"An analogy for the Hox genes can be made to the role of a play director who calls which scene the actors should carry out next. If the play director calls the scenes in the wrong order, the overall play will be presented in the wrong order."*

Hox is an experimental architecture that separates how components coordinate from how their layout is calculated. 

Written in pure functional Python 3.14, it brings together two distinct ideas:

1. **An Interaction Protocol**: A high-level script governing component communication and multi-round negotiation. Built with Multiparty Session Types and choice-guarded recursion, it guarantees deadlock freedom, preserves turn-taking, and prunes uninvolved bystander components from loops.
2. **A Spatial Solver**: A lightweight constraint engine that handles elastic reflow, pushing colliding cards and expanding containers. Built with Sussman Propagator Networks over interval bounds, it settles to a resting point in a few steps with zero coordinate drift.
3. **A Footprint Bridge**: The seam between the two layers. Components make layout decisions using a scoped view (`project_tissue`), ensuring decision logic only sees local measurements and cannot snoop on foreign state.

---

## Core Concept

* **The protocol decides when and who**: the sequence of negotiation phases.
* **The propagator decides where and how much**: the coordinate bounds.
* **Quiescence connects them**: the protocol only advances when the spatial constraints have settled.

```
                     Choice-Guarded Protocol
                   μ(Negotiate) . choice by Sidebar {
                       Retry:  Sidebar -> Main : CounterOffer . Negotiate,
                       Commit: Sidebar -> Main : Accept . end
                   }
                                  │
                       Scoped Projection
                                  ▼
                    Local Endpoint State Machines
                    • Isolated recursion scopes per role
                                  │
                                  ▼
                    Footprint View
                     project_tissue(tissue, footprint)
                                  │
                                  ▼
                     Local Spatial Propagators
                     • separation_constraint (push right)
                     • pin_constraint (zero drift)
                                  │
                                  ▼
                      Structured Solver Outcome
                SolveSuccess | SolveInconsistent | SolveStepLimit
```

---

## Potential Applications

| Domain | How the Architecture Applies | Trade-offs & Fit |
| :--- | :--- | :--- |
| **Interactive & Infinite Canvases** | Generates proposed reflows (cards displacing neighbors, containers resizing to content) from drag and resize gestures. Emits clean batch data (`LayoutPlan`) on pointer release. | **Good Fit**: Solves overlap management locally without global solver lag. |
| **BIM & Spatial Coordination (CAD)** | Local spatial conflict avoidance (beam-duct clearance, rebar spacing). Proposes minimum component adjustments without triggering global re-renders. | **Good Fit for Geometry**: A spatial assistant for layout conflicts, not a structural calculation or FEA engine. |
| **Multi-Agent Systems** | Protocol layer coordinates agent turn-taking and message schemas; monotonic constraint network acts as a shared factual blackboard. | **Plausible Fit**: Prevents conversation loops and fact retraction. |

---

### Conceptual Influences

The architecture draws on three distinct threads in systems design:
* **Christopher Alexander (Generative Sequences)**: Separating the sequential, step-by-step unfolding of a structure from local adaptation to spatial forces. The choreography represents the unfolding sequence; the propagators resolve local forces.
* **Gerald Sussman & Alexey Radul (Propagators)**: Using autonomous, multi-directional constraint networks that settle to a fixed point through local monotonic accumulation, avoiding a central master equation.
* **Alan Kay (Biological Scaling)**: Using a small set of selector directives (Hox genes) to parameterize a large collection of decentralized, locally communicating entities.

---

### Pragmatic Boundaries

* **Good Use Cases**:
  - Local interaction loops on an infinite canvas where cards need spatial rules like elastic displacement, container padding, and zero-drift pins.
  - Interactive modeling assistance that recommends minimum adjustments when components collide, previewing before committing.
  - Decoupled previews where continuous relaxation is cleanly separated from durable, single-batch document writes.
  - Multi-party state transitions that need deadlock-free guarantees without manual lock management.
* **Bad Use Cases & Anti-Patterns**:
  - Core structural analysis: Hox does not solve continuous mechanics equations, stress tensors, nonlinear material yielding, or seismic code checks. It assists with spatial clearance and layout, not structural safety.
  - Everyday CRUD: Forms, user accounts, and database queries where standard request-response pipelines are already well-understood.
  - Distributed network locking: Running session types across peers over WebSockets breaks the offline-first, conflict-free guarantees of CRDTs.

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
1. **Desktop Viewport (720px)**: Sidebar asks for Full Mode [200, 300]px. Fits on Round 1 and commits to 250px.
2. **Tablet Viewport (520px)**: Sidebar asks for Full Mode. Contradiction detected (`SolveInconsistent`). Sidebar chooses Retry and counter-offers Compact Mode [80, 150]px. Fits on Round 2 and commits to 120px.
3. **3-Card Spatial Bump**: Card A bumps Card B from 150px to 220px. Card C (pinned at 600px) has zero drift ([600, 600]).

---

## Running the Test Suite

```bash
python3 -m unittest discover -s tests
```
*17 tests passing in ~0.001s*, verifying semilattice arithmetic, confluence under merge, scoped recursive projection, structured failure modes, zero-drift spatial pinning, and footprint privacy.
