# Hox: Functional Session Projections over Sussman Propagator Networks

> *"Only a tiny fraction of cells contain the master morphogenetic directives; the rest is reactive tissue."*

**Hox** is an experimental architectural prototype written in **pure functional Python 3.14**:
1. **Multiparty Session Types (MPST / Choreographies)**: Immutable Algebraic Data Types (ADTs) representing global protocols, projected via pure pattern-matching recursion into local Communicating Finite State Machines (CFSMs).
2. **Sussman Propagator Networks**: Pure state transformers `State -> State` over an interval join-semilattice $[lo, hi]$, where quiescence is computed via a pure mathematical fixed-point loop ($fix(F)$).
3. **The Hox Bridge**: An immutable `HoxState` snapshot combining discrete session states with continuous lattice states, transformed through pure functions without side-effects.

---

## Functional Architecture

```
                          Global Choreography ADT
                   SendG("Canvas", "Sidebar", ..., cont)
                                    │
                         project(global, role)
                                    ▼
                      Projected Local Endpoint ADTs
             SendL("Main", ...), RecvL("Canvas", ...), ChoiceL
                                    │
                                    ▼
                 Immutable System Snapshot: HoxState
                 ┌───────────────────────────────────┐
                 │ endpoints: { Role: LocalState }   │
                 │ tissue:    { Cell: Interval }     │
                 │ props:     [ State -> State ]     │
                 └─────────────────┬─────────────────┘
                                   │
              settle_tissue(state) │ Pure fixed-point: fix(F)
                                   ▼
                            Settled HoxState
                                   │
               decide_branch(state, decider, predicate)
                                   ▼
                 Deterministic Deadlock-Free Transition
```

---

## Directory Structure

```
hox/
├── propagator/
│   ├── lattice.py          # Pure interval semilattice [lo, hi], merge, plus, minus
│   ├── propagators.py      # Pure state transformers: State -> State (sum_constraint, etc.)
│   └── engine.py           # Pure fixed-point solver: settle(state, propagators) -> (state, steps)
├── session/
│   ├── types.py            # Algebraic Data Types (ADTs): SendG, ChoiceG, EndG, SendL, RecvL...
│   ├── projection.py       # Pure pattern-matching projection: project(Global, role) -> Local
│   └── runtime.py          # Pure transition functions: step_send, step_receive, step_choose
├── bridge/
│   └── functional_bridge.py# Pure system state transformations: inject_constraint, settle_tissue...
└── demo.py                 # Pure pipeline demo of 3-party layout negotiation
```

---

## Running the Demo

Execute the interactive functional demo:

```bash
python3 -m hox.demo
```

Runs the 3-party layout negotiation (`Canvas`, `Sidebar`, `MainContent`):
* **Desktop (720px)**: The geometric tissue settles to $[0, 320]$ for the sidebar. Since $320 \ge 200$, Sidebar chooses branch `Fit` and Main receives `AcceptFit`.
* **Split (480px)**: The geometric tissue settles to $[0, 80]$. Since $80 < 200$, Sidebar chooses branch `Collapse` and Main receives `DoCollapse`, claiming all 480px.

---

## Running the Test Suite

```bash
python3 -m unittest discover -s tests
```
*(All tests execute in ~0.001s, verifying lattice arithmetic, fixed-point convergence, recursive projection, and pure state transitions).*
