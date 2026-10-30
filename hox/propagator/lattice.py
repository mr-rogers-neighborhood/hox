"""Pure functional interval join-semilattice."""

from __future__ import annotations
import math
from dataclasses import dataclass


class ContradictionError(Exception):
    """Raised when an interval contradiction is detected (lo > hi)."""
    pass


@dataclass(frozen=True)
class Interval:
    """Immutable interval [lo, hi] over the reals."""
    lo: float = -math.inf
    hi: float = math.inf

    @classmethod
    def exact(cls, val: float) -> Interval:
        return cls(lo=float(val), hi=float(val))

    @classmethod
    def at_least(cls, val: float) -> Interval:
        return cls(lo=float(val), hi=math.inf)

    @classmethod
    def at_most(cls, val: float) -> Interval:
        return cls(lo=-math.inf, hi=float(val))

    @classmethod
    def unconstrained(cls) -> Interval:
        return cls(-math.inf, math.inf)

    @property
    def is_contradiction(self) -> bool:
        return self.lo > self.hi

    @property
    def is_exact(self) -> bool:
        return not self.is_contradiction and self.lo == self.hi and not math.isinf(self.lo)

    # Convenience method wrappers over pure functions
    def merge(self, other: Interval) -> Interval:
        return merge(self, other)

    def plus(self, other: Interval) -> Interval:
        return plus(self, other)

    def minus(self, other: Interval) -> Interval:
        return minus(self, other)

    def narrows(self, other: Interval) -> bool:
        return narrows(self, other)

    def __str__(self) -> str:
        if self.is_contradiction:
            return f"Contradiction({self.lo} > {self.hi})"
        if self.is_exact:
            return f"[{self.lo:g}]"
        lo_str = "-∞" if math.isinf(self.lo) and self.lo < 0 else f"{self.lo:g}"
        hi_str = "∞" if math.isinf(self.hi) and self.hi > 0 else f"{self.hi:g}"
        return f"[{lo_str}, {hi_str}]"


def merge(a: Interval, b: Interval) -> Interval:
    """Lattice meet (information join): narrowing intersection of two intervals."""
    res = Interval(max(a.lo, b.lo), min(a.hi, b.hi))
    if res.is_contradiction:
        raise ContradictionError(f"Contradiction merging {a} with {b} -> [{res.lo}, {res.hi}]")
    return res


def plus(a: Interval, b: Interval) -> Interval:
    """Interval addition: [a.lo + b.lo, a.hi + b.hi]."""
    return Interval(a.lo + b.lo, a.hi + b.hi)


def minus(a: Interval, b: Interval) -> Interval:
    """Interval subtraction: a - b = [a.lo - b.hi, a.hi - b.lo]."""
    return Interval(a.lo - b.hi, a.hi - b.lo)


def narrows(new_val: Interval, old_val: Interval, eps: float = 1e-9) -> bool:
    """Returns True if new_val contains strictly more information than old_val."""
    return (new_val.lo > old_val.lo + eps) or (new_val.hi < old_val.hi - eps)
