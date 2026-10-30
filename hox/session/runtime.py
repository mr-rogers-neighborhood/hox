"""Pure state-transition functions for local session types."""

from __future__ import annotations
from typing import Tuple, Any
from .types import (
    Local,
    SendL,
    RecvL,
    InternalChoiceL,
    ExternalChoiceL,
    EndL,
    Message,
)


class ProtocolViolationError(Exception):
    """Raised when an action violates the projected session state machine."""
    pass


def step_send(local_state: Local, sender_role: str, to_role: str, label: str, payload: Any = None) -> Tuple[Local, Message]:
    """Pure transition: execute a send obligation, returning (continuation_state, message)."""
    match local_state:
        case SendL(expected_to, expected_label, cont):
            if expected_to != to_role or expected_label != label:
                raise ProtocolViolationError(
                    f"Role '{sender_role}' expected to send '{expected_label}' to '{expected_to}', "
                    f"but attempted to send '{label}' to '{to_role}'"
                )
            msg = Message(sender=sender_role, receiver=to_role, label=label, payload=payload)
            return cont, msg

        case _:
            raise ProtocolViolationError(f"Role '{sender_role}' cannot send in state: {local_state}")


def step_receive(local_state: Local, receiver_role: str, msg: Message) -> Local:
    """Pure transition: execute a receive obligation against incoming message, returning continuation_state."""
    match local_state:
        case RecvL(expected_from, expected_label, cont):
            if expected_from != msg.sender:
                raise ProtocolViolationError(
                    f"Role '{receiver_role}' expected message from '{expected_from}', but got '{msg.sender}'"
                )
            if expected_label != msg.label:
                raise ProtocolViolationError(
                    f"Role '{receiver_role}' expected label '{expected_label}', but got '{msg.label}'"
                )
            return cont

        case _:
            raise ProtocolViolationError(f"Role '{receiver_role}' cannot receive in state: {local_state}")


def step_choose(local_state: Local, decider_role: str, branch_label: str) -> Local:
    """Pure transition: decider selects a branch, returning continuation_state."""
    match local_state:
        case InternalChoiceL(branches):
            if branch_label not in branches:
                raise ProtocolViolationError(
                    f"Role '{decider_role}' cannot select unknown branch '{branch_label}'. Allowed: {list(branches.keys())}"
                )
            return branches[branch_label]

        case _:
            raise ProtocolViolationError(f"Role '{decider_role}' cannot choose branch in state: {local_state}")


def step_follow_choice(local_state: Local, follower_role: str, from_role: str, branch_label: str) -> Local:
    """Pure transition: participant follows decider's choice, returning continuation_state."""
    match local_state:
        case ExternalChoiceL(expected_from, branches):
            if expected_from != from_role:
                raise ProtocolViolationError(
                    f"Role '{follower_role}' expected choice from '{expected_from}', not '{from_role}'"
                )
            if branch_label not in branches:
                raise ProtocolViolationError(
                    f"Role '{follower_role}' cannot follow unknown branch '{branch_label}'. Allowed: {list(branches.keys())}"
                )
            return branches[branch_label]

        case _:
            raise ProtocolViolationError(f"Role '{follower_role}' cannot follow choice in state: {local_state}")


def is_terminated(local_state: Local) -> bool:
    """Check if endpoint has reached End."""
    return isinstance(local_state, EndL)
