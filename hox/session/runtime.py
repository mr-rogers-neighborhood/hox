"""Pure state-transition functions for local session types with recursion support."""

from __future__ import annotations
from typing import Tuple, Any, Dict, Optional
from .types import (
    Local,
    SendL,
    RecvL,
    InternalChoiceL,
    ExternalChoiceL,
    RecL,
    VarL,
    EndL,
    Message,
)


class ProtocolViolationError(Exception):
    """Raised when an action violates the projected session state machine."""
    pass


def unroll(state: Local, env: Optional[Dict[str, Local]] = None) -> Tuple[Local, Dict[str, Local]]:
    """Recursively expand RecL loop heads and VarL jumps using an immutable environment."""
    current_env = dict(env or {})
    curr = state

    while True:
        match curr:
            case RecL(tag, body):
                current_env[tag] = curr
                curr = body
            case VarL(tag):
                if tag not in current_env:
                    raise ProtocolViolationError(f"Unbound recursion variable '{tag}' in state.")
                curr = current_env[tag]
            case _:
                return curr, current_env


def step_send(
    local_state: Local,
    sender_role: str,
    to_role: str,
    label: str,
    payload: Any = None,
    env: Optional[Dict[str, Local]] = None
) -> Tuple[Local, Message, Dict[str, Local]]:
    """Pure transition: execute a send obligation, returning (continuation_state, message, new_env)."""
    norm_state, current_env = unroll(local_state, env)

    match norm_state:
        case SendL(expected_to, expected_label, cont):
            if expected_to != to_role or expected_label != label:
                raise ProtocolViolationError(
                    f"Role '{sender_role}' expected to send '{expected_label}' to '{expected_to}', "
                    f"but attempted to send '{label}' to '{to_role}'"
                )
            msg = Message(sender=sender_role, receiver=to_role, label=label, payload=payload)
            next_state, next_env = unroll(cont, current_env)
            return next_state, msg, next_env

        case _:
            raise ProtocolViolationError(f"Role '{sender_role}' cannot send in state: {norm_state}")


def step_receive(
    local_state: Local,
    receiver_role: str,
    msg: Message,
    env: Optional[Dict[str, Local]] = None
) -> Tuple[Local, Dict[str, Local]]:
    """Pure transition: execute a receive obligation against incoming message, returning (continuation_state, new_env)."""
    norm_state, current_env = unroll(local_state, env)

    match norm_state:
        case RecvL(expected_from, expected_label, cont):
            if expected_from != msg.sender:
                raise ProtocolViolationError(
                    f"Role '{receiver_role}' expected message from '{expected_from}', but got '{msg.sender}'"
                )
            if expected_label != msg.label:
                raise ProtocolViolationError(
                    f"Role '{receiver_role}' expected label '{expected_label}', but got '{msg.label}'"
                )
            next_state, next_env = unroll(cont, current_env)
            return next_state, next_env

        case _:
            raise ProtocolViolationError(f"Role '{receiver_role}' cannot receive in state: {norm_state}")


def step_choose(
    local_state: Local,
    decider_role: str,
    branch_label: str,
    env: Optional[Dict[str, Local]] = None
) -> Tuple[Local, Dict[str, Local]]:
    """Pure transition: decider selects a branch, returning (continuation_state, new_env)."""
    norm_state, current_env = unroll(local_state, env)

    match norm_state:
        case InternalChoiceL(branches):
            if branch_label not in branches:
                raise ProtocolViolationError(
                    f"Role '{decider_role}' cannot select unknown branch '{branch_label}'. Allowed: {list(branches.keys())}"
                )
            next_state, next_env = unroll(branches[branch_label], current_env)
            return next_state, next_env

        case _:
            raise ProtocolViolationError(f"Role '{decider_role}' cannot choose branch in state: {norm_state}")


def step_follow_choice(
    local_state: Local,
    follower_role: str,
    from_role: str,
    branch_label: str,
    env: Optional[Dict[str, Local]] = None
) -> Tuple[Local, Dict[str, Local]]:
    """Pure transition: participant follows decider's choice, returning (continuation_state, new_env)."""
    norm_state, current_env = unroll(local_state, env)

    match norm_state:
        case ExternalChoiceL(expected_from, branches):
            if expected_from != from_role:
                raise ProtocolViolationError(
                    f"Role '{follower_role}' expected choice from '{expected_from}', not '{from_role}'"
                )
            if branch_label not in branches:
                raise ProtocolViolationError(
                    f"Role '{follower_role}' cannot follow unknown branch '{branch_label}'. Allowed: {list(branches.keys())}"
                )
            next_state, next_env = unroll(branches[branch_label], current_env)
            return next_state, next_env

        case _:
            raise ProtocolViolationError(f"Role '{follower_role}' cannot follow choice in state: {norm_state}")


def is_terminated(local_state: Local, env: Optional[Dict[str, Local]] = None) -> bool:
    """Check if endpoint has reached End."""
    norm, _ = unroll(local_state, env)
    return isinstance(norm, EndL)
