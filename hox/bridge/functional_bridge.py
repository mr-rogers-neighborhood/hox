"""Pure functional bridge with per-role recursion environments and footprint views."""

from __future__ import annotations
from typing import Mapping, Sequence, Tuple, Callable, Any, FrozenSet, Dict
from dataclasses import dataclass, field
from hox.propagator import (
    Interval,
    Propagator,
    State,
    inject,
    settle,
    SolveResult,
    SolveSuccess,
    SolveInconsistent,
    SolveStepLimit,
)
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
    - envs: per-role recursion environments (role -> (tag -> Local))
    """
    endpoints: Mapping[str, Local]
    tissue: Mapping[str, Interval]
    propagators: Sequence[Propagator] = field(default_factory=tuple)
    envs: Mapping[str, Mapping[str, Local]] = field(default_factory=dict)

    def is_all_terminated(self) -> bool:
        return all(
            is_terminated(st, dict(self.envs.get(role, {})))
            for role, st in self.endpoints.items()
        )


def project_tissue(tissue: Mapping[str, Interval], footprint: FrozenSet[str]) -> Mapping[str, Interval]:
    """Slice the global tissue down to ONLY the cells in the declared footprint."""
    return {cell: tissue[cell] for cell in footprint if cell in tissue}


def inject_constraint(system: HoxState, cell: str, interval: Interval) -> HoxState:
    """Pure function: inject a constraint into the propagator tissue, returning a new HoxState."""
    new_tissue = inject(system.tissue, cell, interval)
    return HoxState(
        endpoints=system.endpoints,
        tissue=new_tissue,
        propagators=system.propagators,
        envs=system.envs
    )


def settle_tissue(system: HoxState, max_steps: int | None = None) -> Tuple[HoxState, SolveResult]:
    """Pure function: relax the propagator tissue to quiescence (fixed point)."""
    result = settle(system.tissue, system.propagators, max_steps=max_steps)
    if isinstance(result, SolveSuccess):
        new_system = HoxState(
            endpoints=system.endpoints,
            tissue=result.tissue,
            propagators=system.propagators,
            envs=system.envs
        )
        return new_system, result
    return system, result


def send_message(
    system: HoxState,
    sender: str,
    receiver: str,
    label: str,
    payload: Any = None
) -> Tuple[HoxState, Message]:
    """Pure function: sender advances its session state and emits an immutable Message."""
    sender_state = system.endpoints[sender]
    sender_env = dict(system.envs.get(sender, {}))
    next_sender_state, msg, next_sender_env = step_send(
        sender_state, sender, receiver, label, payload, sender_env
    )

    new_endpoints = dict(system.endpoints)
    new_endpoints[sender] = next_sender_state

    new_envs = dict(system.envs)
    new_envs[sender] = next_sender_env

    return (
        HoxState(
            endpoints=new_endpoints,
            tissue=system.tissue,
            propagators=system.propagators,
            envs=new_envs
        ),
        msg
    )


def receive_message(system: HoxState, receiver: str, msg: Message) -> HoxState:
    """Pure function: receiver advances its session state upon consuming msg."""
    recv_state = system.endpoints[receiver]
    recv_env = dict(system.envs.get(receiver, {}))
    next_recv_state, next_recv_env = step_receive(
        recv_state, receiver, msg, recv_env
    )

    new_endpoints = dict(system.endpoints)
    new_endpoints[receiver] = next_recv_state

    new_envs = dict(system.envs)
    new_envs[receiver] = next_recv_env

    return HoxState(
        endpoints=new_endpoints,
        tissue=system.tissue,
        propagators=system.propagators,
        envs=new_envs
    )


def decide_branch(
    system: HoxState,
    decider: str,
    footprint: FrozenSet[str],
    decision_fn: Callable[[Mapping[str, Interval]], str]
) -> Tuple[HoxState, str]:
    """Pure function: decider inspects its local footprint view and chooses a branch."""
    local_view = project_tissue(system.tissue, footprint)
    chosen_branch = decision_fn(local_view)

    decider_state = system.endpoints[decider]
    decider_env = dict(system.envs.get(decider, {}))
    next_state, next_decider_env = step_choose(
        decider_state, decider, chosen_branch, decider_env
    )

    new_endpoints = dict(system.endpoints)
    new_endpoints[decider] = next_state

    new_envs = dict(system.envs)
    new_envs[decider] = next_decider_env

    return (
        HoxState(
            endpoints=new_endpoints,
            tissue=system.tissue,
            propagators=system.propagators,
            envs=new_envs
        ),
        chosen_branch
    )


def follow_branch(system: HoxState, follower: str, decider: str, branch: str) -> HoxState:
    """Pure function: follower adopts external choice branch from decider."""
    follower_state = system.endpoints[follower]
    follower_env = dict(system.envs.get(follower, {}))
    next_state, next_follower_env = step_follow_choice(
        follower_state, follower, decider, branch, follower_env
    )

    new_endpoints = dict(system.endpoints)
    new_endpoints[follower] = next_state

    new_envs = dict(system.envs)
    new_envs[follower] = next_follower_env

    return HoxState(
        endpoints=new_endpoints,
        tissue=system.tissue,
        propagators=system.propagators,
        envs=new_envs
    )
