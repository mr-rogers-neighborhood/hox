# Hox

Hox is an experimental architecture that separates how interactive components coordinate from how their spatial layout is calculated.

In typical UI architectures, state machines and layout solvers are tightly coupled. Hox decouples them into two complementary planes connected by a formal boundary:

1. **Control Plane (Choreography)**: A high-level protocol governing multi-round negotiation, turn-taking, and fallback branches. Modeled with multiparty session types and choice-guarded recursion.
2. **Data Plane (Propagator Network)**: A continuous constraint engine handling elastic reflow, collision bumping, and container sizing. Built on Sussman propagator networks over interval semilattices.
3. **The Footprint Boundary**: A scoped projection (`project_tissue`) ensuring negotiating components only observe local bounding intervals and cannot inspect foreign state.

* **The protocol decides when and who**: the sequence of negotiation phases.
* **The propagator decides where and how much**: coordinate bounds and continuous relaxation.
* **Quiescence connects them**: the protocol only advances once the spatial network settles to a fixed point.

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

## Scope & Current Status

This repository is a reference prototype exploring the boundary between session choreographies and propagator networks.

* **Cluster Scale**: Exercised by the demo and test suite on 2–4 node clusters; dense cyclic networks not benchmarked.
* **In-Process Runtime**: The session runtime executes in-memory within a single process. It models the local interaction lifecycle (gesture -> preview -> batch commit); it does not implement a distributed wire protocol over network sockets.
* **Purity by Convention**: Implemented in Python 3.14 using frozen dataclasses and immutable transitions. Purity is maintained by architectural convention rather than compiler enforcement.
* **Conceptual Framing**: The biological Hox analogy describes the systems relationship (a discrete regulatory control plane parameterizing a continuous spatial tissue).

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
* **Alan Kay (Biological Scaling)**: Using a small set of selector directives to parameterize a large collection of decentralized, locally communicating entities.

---

### Pragmatic Boundaries

* **Good Use Cases**:
  - Local interaction loops on an infinite canvas where cards need spatial rules like elastic displacement, container padding, and zero-drift pins.
  - Interactive modeling assistance that recommends minimum adjustments when components collide, previewing before committing.
  - Decoupled previews where continuous relaxation is cleanly separated from durable, single-batch document writes.
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
