"""Pure recursive projection from Global Choreographies to Local Session Types with Scope Tracking."""

from __future__ import annotations
from typing import List, Set, FrozenSet
from .types import (
    Global,
    SendG,
    ChoiceG,
    RecG,
    VarG,
    EndG,
    Local,
    SendL,
    RecvL,
    InternalChoiceL,
    ExternalChoiceL,
    RecL,
    VarL,
    EndL,
)


def project(global_type: Global, role: str, scope: FrozenSet[str] = frozenset()) -> Local:
    """Project a global choreography onto a role, tracking active recursion scopes.
    
    If role does not participate in a loop body, it cleanly omits RecL and projects VarG to EndL.
    """
    match global_type:
        case SendG(sender, receiver, label, cont):
            if role == sender:
                return SendL(to_role=receiver, label=label, cont=project(cont, role, scope))
            elif role == receiver:
                return RecvL(from_role=sender, label=label, cont=project(cont, role, scope))
            else:
                # Role not participating in this message; skip directly to continuation
                return project(cont, role, scope)

        case ChoiceG(decider, branches):
            projected_branches = {
                label: project(branch_global, role, scope)
                for label, branch_global in branches.items()
            }
            if role == decider:
                return InternalChoiceL(branches=projected_branches)
            else:
                first = next(iter(projected_branches.values()))
                if all(b == first for b in projected_branches.values()):
                    return first
                return ExternalChoiceL(from_role=decider, branches=projected_branches)

        case RecG(tag, body):
            # If the role does not participate anywhere in the loop body, it skips it
            if role not in extract_roles(body):
                return EndL()

            body_proj = project(body, role, scope | {tag})
            # Only wrap in RecL if the role actually loops back via VarL(tag)
            if _has_free_var(body_proj, tag):
                return RecL(tag=tag, body=body_proj)
            return body_proj

        case VarG(tag):
            # Only loop back if tag is in the role's active recursion scope
            if tag in scope:
                return VarL(tag=tag)
            return EndL()

        case EndG():
            return EndL()


def _has_free_var(local_type: Local, tag: str) -> bool:
    """Check if local type contains a free occurrence of VarL(tag)."""
    match local_type:
        case VarL(t):
            return t == tag
        case SendL(_, _, cont) | RecvL(_, _, cont):
            return _has_free_var(cont, tag)
        case InternalChoiceL(branches) | ExternalChoiceL(_, branches):
            return any(_has_free_var(b, tag) for b in branches.values())
        case RecL(t, body):
            if t == tag:
                return False  # Shadowed
            return _has_free_var(body, tag)
        case EndL():
            return False


def extract_roles(global_type: Global) -> List[str]:
    """Collect all participant roles involved in a global choreography."""
    def _collect(g: Global) -> Set[str]:
        match g:
            case SendG(s, r, _, cont):
                return {s, r} | _collect(cont)
            case ChoiceG(d, branches):
                roles = {d}
                for b in branches.values():
                    roles |= _collect(b)
                return roles
            case RecG(_, body):
                return _collect(body)
            case VarG(_):
                return set()
            case EndG():
                return set()

    return sorted(list(_collect(global_type)))
