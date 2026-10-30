"""Pure functional fixed-point solver (quiescence engine) for propagator networks."""

from __future__ import annotations
from typing import Sequence, Tuple, Dict
from .lattice import Interval
from .propagators import State, Propagator


def settle(
    state: State,
    propagators: Sequence[Propagator],
    max_steps: int = 1000
) -> Tuple[Dict[str, Interval], int]:
    """Pure fixed-point solver for propagator networks.
    
    Repeatedly applies propagators in sequence until the state reaches quiescence
    (a mathematical fixed point where F(state) == state).
    
    Returns:
        (settled_state, steps_taken)
    """
    current = dict(state)
    for step in range(1, max_steps + 1):
        prev = current
        for prop in propagators:
            current = prop(current)
        # Fixed point reached: no cell intervals narrowed in this cycle
        if current == prev:
            return current, step

    raise RuntimeError(f"Propagator network failed to settle within {max_steps} steps.")

