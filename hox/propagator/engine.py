"""Pure functional fixed-point solver with structured failure results."""

from __future__ import annotations
from typing import Sequence, Mapping, Union, Dict
from dataclasses import dataclass
from .lattice import Interval, ContradictionError
from .propagators import State, Propagator


@dataclass(frozen=True)
class SolveSuccess:
    """The propagator network successfully reached quiescence (a stable fixed point)."""
    tissue: Mapping[str, Interval]
    steps: int

    def __str__(self) -> str:
        cell_strs = ", ".join(f"{k}: {v}" for k, v in self.tissue.items())
        return f"SolveSuccess(steps={self.steps}, tissue={{{cell_strs}}})"


@dataclass(frozen=True)
class SolveInconsistent:
    """The constraints conflicted (e.g., trying to force a pinned card into an impossible spot)."""
    conflict: str

    def __str__(self) -> str:
        return f"SolveInconsistent({self.conflict})"


@dataclass(frozen=True)
class SolveStepLimit:
    """The network exceeded its step bound without settling."""
    steps: int
    limit: int

    def __str__(self) -> str:
        return f"SolveStepLimit(steps={self.steps}, limit={self.limit})"


SolveResult = Union[SolveSuccess, SolveInconsistent, SolveStepLimit]


def settle(
    state: State,
    propagators: Sequence[Propagator],
    max_steps: int | None = None
) -> SolveResult:
    """Pure fixed-point solver for propagator networks with structured error reporting.
    
    Repeatedly applies propagators in sequence until the state reaches quiescence
    (a mathematical fixed point where F(state) == state).
    
    Returns:
        SolveSuccess | SolveInconsistent | SolveStepLimit
    """
    current = dict(state)
    # Defensible step limit based on state size and constraints
    limit = max_steps if max_steps is not None else max(50, 2 * len(state) * max(1, len(propagators)))

    for step in range(1, limit + 1):
        prev = current
        try:
            for prop in propagators:
                current = prop(current)
        except ContradictionError as err:
            return SolveInconsistent(conflict=str(err))

        # Fixed point reached: no cell intervals narrowed in this cycle
        if current == prev:
            return SolveSuccess(tissue=current, steps=step)

    return SolveStepLimit(steps=limit, limit=limit)
