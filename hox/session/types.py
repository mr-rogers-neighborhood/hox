"""Algebraic Data Types (ADTs) for Global and Local Session Types."""

from __future__ import annotations
from typing import Dict, Union, Any, Optional
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Global Session Types (The Choreography / Hox Gene)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SendG:
    """Directed interaction: sender -> receiver : label, continuing with cont."""
    sender: str
    receiver: str
    label: str
    cont: Global

    def __str__(self) -> str:
        return f"{self.sender} -> {self.receiver} : {self.label} . {self.cont}"


@dataclass(frozen=True)
class ChoiceG:
    """Internal branching point decided by decider offering labeled branches."""
    decider: str
    branches: Dict[str, Global]

    def __str__(self) -> str:
        br_str = ", ".join(f"{lbl}: ({g})" for lbl, g in self.branches.items())
        return f"choice by {self.decider} {{ {br_str} }}"


@dataclass(frozen=True)
class EndG:
    """Protocol completion."""
    def __str__(self) -> str:
        return "end"


Global = Union[SendG, ChoiceG, EndG]


# ---------------------------------------------------------------------------
# Local Session Types (Projected Communicating Automata)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SendL:
    """Local send obligation: !to_role<label> . cont"""
    to_role: str
    label: str
    cont: Local

    def __str__(self) -> str:
        return f"!{self.to_role}<{self.label}> . {self.cont}"


@dataclass(frozen=True)
class RecvL:
    """Local receive obligation: ?from_role<label> . cont"""
    from_role: str
    label: str
    cont: Local

    def __str__(self) -> str:
        return f"?{self.from_role}<{self.label}> . {self.cont}"


@dataclass(frozen=True)
class InternalChoiceL:
    """Local choice obligation: ⊕ { label: cont }"""
    branches: Dict[str, Local]

    def __str__(self) -> str:
        br_str = ", ".join(f"{lbl}: {cont}" for lbl, cont in self.branches.items())
        return f"⊕ {{ {br_str} }}"


@dataclass(frozen=True)
class ExternalChoiceL:
    """Local branching obligation following decider: &(from_role) { label: cont }"""
    from_role: str
    branches: Dict[str, Local]

    def __str__(self) -> str:
        br_str = ", ".join(f"{lbl}: {cont}" for lbl, cont in self.branches.items())
        return f"&({self.from_role}) {{ {br_str} }}"


@dataclass(frozen=True)
class EndL:
    """Local endpoint termination."""
    def __str__(self) -> str:
        return "end"


Local = Union[SendL, RecvL, InternalChoiceL, ExternalChoiceL, EndL]


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Message:
    """Immutable protocol message exchanged between endpoints."""
    sender: str
    receiver: str
    label: str
    payload: Any = None

    def __str__(self) -> str:
        p_str = f"({self.payload})" if self.payload is not None else ""
        return f"[{self.sender} -> {self.receiver} : {self.label}{p_str}]"

