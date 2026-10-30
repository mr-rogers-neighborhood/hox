"""Pure functional bridge: coordinating session states with propagator lattice states."""

from __future__ import annotations
from typing import Mapping, Sequence, Tuple, Callable, Any
from dataclasses import dataclass, field
from hox.propagator import Interval, Propagator, State, inject, settle
from hox.session import (
    Local,
    Message,
    step_send,
    step_receive,
    step_choose,
    step_follow_choice,
    is_terminated,
)


@dataclass(frozen=True)
class HoxState:
    """An immutable snapshot of the entire hybrid system.
    
    Contains:
    - endpoints: discrete session CFSM states for each participant (role -> Local)
    - tissue: continuous interval lattice state (cell_name -> Interval)
    - propagators: active multi-directional relations over the tissue
    """
    endpoints: Mapping[str, Local]
    tissue: Mapping[str, Interval]
    propagators: Sequence[Propagator] = field(default_factory=tuple)

    def is_all_terminated(self) -> bool:
        return all(is_terminated(st) for st in self.endpoints.values())


def inject_constraint(system: HoxState, cell: str, interval: Interval) -> HoxState:
    """Pure function: inject a constraint into the propagator tissue, returning a new HoxState."""
    new_tissue = inject(system.tissue, cell, interval)
    return HoxState(
        endpoints=system.endpoints,
        tissue=new_tissue,
        propagators=system.propagators
    )


def settle_tissue(system: HoxState, max_steps: int = 1000) -> Tuple[HoxState, int]:
    """Pure function: relax the propagator tissue to quiescence (fixed point)."""
    settled_tissue, steps = settle(system.tissue, system.propagators, max_steps=max_steps)
    return (
        HoxState(
            endpoints=system.endpoints,
            tissue=settled_tissue,
            propagators=system.propagators
        ),
        steps
    )


def send_message(
    system: HoxState,
    sender: str,
    receiver: str,
    label: str,
    payload: Any = None
) -> Tuple[HoxState, Message]:
    """Pure function: sender advances its session state and emits an immutable Message."""
    sender_state = system.endpoints[sender]
    next_sender_state, msg = step_send(sender_state, sender, receiver, label, payload)

    new_endpoints = dict(system.endpoints)
    new_endpoints[sender] = next_sender_state

    return (
        HoxState(
            endpoints=new_endpoints,
            tissue=system.tissue,
            propagators=system.propagators
        ),
        msg
    )


def receive_message(system: HoxState, receiver: str, msg: Message) -> HoxState:
    """Pure function: receiver advances its session state upon consuming msg."""
    recv_state = system.endpoints[receiver]
    next_recv_state = step_receive(recv_state, receiver, msg)

    new_endpoints = dict(system.endpoints)
    new_endpoints[receiver] = next_recv_state

    return HoxState(
        endpoints=new_endpoints,
        tissue=system.tissue,
        propagators=system.propagators
    )


def decide_branch(
    system: HoxState,
    decider: str,
    decision_fn: Callable[[Mapping[str, Interval]], str]
) -> Tuple[HoxState, str]:
    """Pure function: decider inspects the settled tissue and chooses an internal branch."""
    chosen_branch = decision_fn(system.tissue)
    decider_state = system.endpoints[decider]
    next_state = step_choose(decider_state, decider, chosen_branch)

    new_endpoints = dict(system.endpoints)
    new_endpoints[decider] = next_state

    return (
        HoxState(
            endpoints=new_endpoints,
            tissue=system.tissue,
            propagators=system.propagators
        ),
        chosen_branch
    )


def follow_branch(system: HoxState, follower: str, decider: str, branch: str) -> HoxState:
    """Pure function: follower adopts external choice branch from decider."""
    follower_state = system.endpoints[follower]
    next_state = step_follow_choice(follower_state, follower, decider, branch)

    new_endpoints = dict(system.endpoints)
    new_endpoints[follower] = next_state

    return HoxState(
        endpoints=new_endpoints,
        tissue=system.tissue,
        propagators=system.propagators
    )

