"""Choreographic Global Type DSL for defining multi-party interaction protocols."""

from __future__ import annotations
from typing import List, Dict, Callable, Optional, Union
from dataclasses import dataclass, field


@dataclass
class GlobalSend:
    """A directed message exchange from sender to receiver with a label."""
    sender: str
    receiver: str
    label: str
    payload_type: str = "any"

    def __str__(self) -> str:
        return f"{self.sender} -> {self.receiver} : {self.label}"


@dataclass
class GlobalChoice:
    """An internal decision made by decider, offering labeled branches to participants."""
    decider: str
    branches: Dict[str, GlobalType]

    def __str__(self) -> str:
        branch_strs = [f"{label}: ({g})" for label, g in self.branches.items()]
        return f"choice by {self.decider} {{ {', '.join(branch_strs)} }}"


@dataclass
class GlobalEnd:
    """Protocol completion."""
    def __str__(self) -> str:
        return "end"


GlobalStep = Union[GlobalSend, GlobalChoice, GlobalEnd]


class GlobalType:
    """A choreographic protocol specification (MPST Global Type)."""

    def __init__(self, name: str = "Protocol", steps: Optional[List[GlobalStep]] = None):
        self.name = name
        self.steps: List[GlobalStep] = steps if steps is not None else []

    def send(self, sender: str, receiver: str, label: str, payload_type: str = "any") -> GlobalType:
        """Append a send step: sender -> receiver : label."""
        new_steps = list(self.steps)
        new_steps.append(GlobalSend(sender, receiver, label, payload_type))
        return GlobalType(self.name, new_steps)

    def choice(
        self,
        decider: str,
        branches_fn: Dict[str, Callable[[GlobalType], GlobalType]]
    ) -> GlobalType:
        """Append a branching point decided by decider."""
        built_branches: Dict[str, GlobalType] = {}
        for label, builder in branches_fn.items():
            sub_proto = builder(GlobalType(f"{self.name}_{label}"))
            built_branches[label] = sub_proto

        new_steps = list(self.steps)
        new_steps.append(GlobalChoice(decider, built_branches))
        return GlobalType(self.name, new_steps)

    def end(self) -> GlobalType:
        new_steps = list(self.steps)
        new_steps.append(GlobalEnd())
        return GlobalType(self.name, new_steps)

    def roles(self) -> List[str]:
        """Collect all distinct participant roles in the protocol."""
        found = set()
        for s in self.steps:
            if isinstance(s, GlobalSend):
                found.add(s.sender)
                found.add(s.receiver)
            elif isinstance(s, GlobalChoice):
                found.add(s.decider)
                for branch in s.branches.values():
                    found.update(branch.roles())
        return sorted(list(found))

    def __str__(self) -> str:
        steps_str = " . ".join(str(s) for s in self.steps)
        return f"{self.name} = {steps_str}"

