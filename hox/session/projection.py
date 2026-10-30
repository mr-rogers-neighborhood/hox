"""Pure recursive projection from Global Choreographies to Local Session Types."""

from __future__ import annotations
from typing import List, Set
from .types import (
    Global,
    SendG,
    ChoiceG,
    EndG,
    Local,
    SendL,
    RecvL,
    InternalChoiceL,
    ExternalChoiceL,
    EndL,
)


def project(global_type: Global, role: str) -> Local:
    """Project a global choreographic type onto a specific participant role using pattern matching."""
    match global_type:
        case SendG(sender, receiver, label, cont):
            if role == sender:
                return SendL(to_role=receiver, label=label, cont=project(cont, role))
            elif role == receiver:
                return RecvL(from_role=sender, label=label, cont=project(cont, role))
            else:
                # Role not participating in this message; skip directly to continuation
                return project(cont, role)

        case ChoiceG(decider, branches):
            projected_branches = {
                label: project(branch_global, role)
                for label, branch_global in branches.items()
            }
            if role == decider:
                return InternalChoiceL(branches=projected_branches)
            else:
                # If all branches project to the exact same behavior for this role,
                # the role does not need to participate in the external choice.
                first = next(iter(projected_branches.values()))
                if all(b == first for b in projected_branches.values()):
                    return first
                return ExternalChoiceL(from_role=decider, branches=projected_branches)

        case EndG():
            return EndL()


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
            case EndG():
                return set()

    return sorted(list(_collect(global_type)))

