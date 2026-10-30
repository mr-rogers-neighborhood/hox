"""Functional propagators as pure state transformers: State -> State."""

from __future__ import annotations
from typing import Mapping, Callable, Dict
from .lattice import Interval, merge, plus, minus

# State is an immutable-friendly mapping from cell names to intervals
State = Mapping[str, Interval]

# A Propagator is simply a pure function: State -> State
Propagator = Callable[[State], State]


def inject(state: State, cell: str, interval: Interval) -> Dict[str, Interval]:
    """Pure function: return a new state with interval merged into cell."""
    current = state.get(cell, Interval.unconstrained())
    merged = merge(current, interval)
    new_state = dict(state)
    new_state[cell] = merged
    return new_state


def sum_constraint(a: str, b: str, c: str) -> Propagator:
    """Multi-directional sum relation: A + B = C.
    
    Returns a pure state transformer that deduces:
    - C = A + B
    - A = C - B
    - B = C - A
    """
    def prop(state: State) -> State:
        val_a = state.get(a, Interval.unconstrained())
        val_b = state.get(b, Interval.unconstrained())
        val_c = state.get(c, Interval.unconstrained())

        # Forward: C = A + B
        implied_c = plus(val_a, val_b)
        new_c = merge(val_c, implied_c)

        # Backward: A = C - B
        implied_a = minus(val_c, val_b)
        new_a = merge(val_a, implied_a)

        # Backward: B = C - A
        implied_b = minus(val_c, val_a)
        new_b = merge(val_b, implied_b)

        # If any value changed, return a new state
        if new_a != val_a or new_b != val_b or new_c != val_c:
            next_state = dict(state)
            next_state[a] = new_a
            next_state[b] = new_b
            next_state[c] = new_c
            return next_state

        return state

    return prop


def bounds_constraint(cell: str, lo: float = -float('inf'), hi: float = float('inf')) -> Propagator:
    """Clamps or narrows a cell within [lo, hi]."""
    bounds = Interval(lo, hi)

    def prop(state: State) -> State:
        current = state.get(cell, Interval.unconstrained())
        merged = merge(current, bounds)
        if merged != current:
            next_state = dict(state)
            next_state[cell] = merged
            return next_state
        return state

    return prop
