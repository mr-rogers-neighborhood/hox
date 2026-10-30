"""Hox v2 Interactive Demo: Choice-Guarded Recursion, Privacy Footprints, and Spatial Pinning.

Demonstrates:
1. 3-Round Recursive Counter-Offer Negotiation (Full -> Compact -> Collapsed)
2. The 'Curtains Closed' Footprint Privacy Rule (No Foreign Cell Snooping)
3. 3-Card Spatial Bump & Zero-Drift Pinning (Card A pushes B, C stays perfectly still)
"""

from __future__ import annotations
from typing import Mapping
from hox.session import (
    Global,
    SendG,
    ChoiceG,
    RecG,
    VarG,
    EndG,
    project,
    extract_roles,
)
from hox.propagator import (
    Interval,
    sum_constraint,
    separation_constraint,
    pin_constraint,
    settle,
    SolveSuccess,
)
from hox.bridge import (
    HoxState,
    project_tissue,
    inject_constraint,
    settle_tissue,
    send_message,
    receive_message,
    decide_branch,
    follow_branch,
)

BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RESET = "\033[0m"


def print_banner():
    print(f"{BOLD}{MAGENTA}")
    print("  _   _  _____  __   __   v2.0")
    print(" | | | |/ _ \\ \\/ /  Choreographic Session Projections")
    print(" | |_| | | | >  <   over Sussman Propagator Networks")
    print(" |  _  | |_| / /\\ \\  (Airtight, Scoped & Recursive)")
    print(" |_| |_|\\___/_/  \\_\\")
    print(f"{RESET}")


def render_ascii_layout(canvas_w: float, sidebar_w: float, main_w: float, mode: str):
    total_cols = 50
    scale = total_cols / canvas_w if canvas_w > 0 else 1
    s_cols = int(round(sidebar_w * scale))
    m_cols = total_cols - s_cols

    print(f"{BOLD}Resulting Layout ({mode} - {canvas_w:g}px Total):{RESET}")
    print("┌" + "─" * s_cols + "┬" + "─" * m_cols + "┐")
    if s_cols > 0:
        s_label = f"Nav({sidebar_w:g}px)"[:s_cols].center(s_cols)
    else:
        s_label = ""
    m_label = f"Main Reading Area ({main_w:g}px)"[:m_cols].center(m_cols)
    print(f"│{s_label}│{m_label}│")
    print("└" + "─" * s_cols + "┴" + "─" * m_cols + "┘\n")


def run_recursive_negotiation_demo(viewport_name: str, canvas_width: float):
    print(f"\n{BOLD}{CYAN}{'═' * 70}{RESET}")
    print(f"{BOLD}{CYAN}  SCENARIO 1: {viewport_name} (Canvas = {canvas_width}px){RESET}")
    print(f"{BOLD}{CYAN}{'═' * 70}{RESET}\n")

    # 1. Define Choice-Guarded Recursive Protocol
    # Sidebar can Retry (counter-offer) or Commit (accept size)
    protocol = SendG(
        sender="Canvas",
        receiver="Sidebar",
        label="Init",
        cont=SendG(
            sender="Canvas",
            receiver="Main",
            label="Init",
            cont=RecG(
                tag="Negotiate",
                body=ChoiceG(
                    decider="Sidebar",
                    branches={
                        "Retry": SendG("Sidebar", "Main", "CounterOffer", VarG("Negotiate")),
                        "Commit": SendG("Sidebar", "Main", "Accept", EndG()),
                    }
                )
            )
        )
    )

    print(f"{BOLD}{YELLOW}▶ Protocol Definition (Choice-Guarded Loop):{RESET}")
    print(f"  {protocol}\n")

    # 2. Project onto Roles with Scope Tracking
    endpoints = {
        "Canvas": project(protocol, "Canvas"),
        "Sidebar": project(protocol, "Sidebar"),
        "Main": project(protocol, "Main"),
    }
    print(f"{BOLD}{YELLOW}▶ Projected Local Endpoints:{RESET}")
    for role, local_type in endpoints.items():
        print(f"  {role:8}: {local_type}")
    print()

    # 3. Setup Immutable Initial System
    tissue = {
        "CanvasWidth": Interval.exact(canvas_width),
        "SidebarWidth": Interval.unconstrained(),
        "MainWidth": Interval.unconstrained(),
    }
    props = [sum_constraint("SidebarWidth", "MainWidth", "CanvasWidth")]
    sys = HoxState(endpoints=endpoints, tissue=tissue, propagators=props)

    # 4. Canvas sends Init
    sys, msg1 = send_message(sys, "Canvas", "Sidebar", "Init", payload=canvas_width)
    sys, msg2 = send_message(sys, "Canvas", "Main", "Init", payload=canvas_width)
    sys = receive_message(sys, "Sidebar", msg1)
    sys = receive_message(sys, "Main", msg2)

    # Main demands at least 400px (or as much as possible on phones)
    main_floor = min(400.0, canvas_width - 20.0)
    sys = inject_constraint(sys, "MainWidth", Interval.at_least(main_floor))

    # The Negotiation Fallback Ladder: Full (250px) -> Compact (120px) -> Collapsed (0px)
    ladder = [
        {"name": "Full Mode", "desired": Interval(200.0, 300.0), "commit": 250.0},
        {"name": "Compact Mode", "desired": Interval(80.0, 150.0), "commit": 120.0},
        {"name": "Collapsed Mode", "desired": Interval.exact(0.0), "commit": 0.0},
    ]

    footprint = frozenset(["SidebarWidth"])
    attempt = 0
    final_mode = "Unknown"

    while True:
        target = ladder[attempt]
        round_num = attempt + 1
        print(f"{BOLD}── Round {round_num}: Sidebar Proposes {target['name']} {target['desired']} ──{RESET}")

        # Inject tentative proposal into tissue
        sys_tentative = inject_constraint(sys, "SidebarWidth", target["desired"])
        sys_tentative, res = settle_tissue(sys_tentative)

        # Can target width fit?
        can_fit = (
            isinstance(res, SolveSuccess)
            and (target["name"] == "Collapsed Mode" or res.tissue["SidebarWidth"].hi >= target["desired"].lo)
        )

        if can_fit:
            # Fits! Commit and exit loop
            print(f"  Tissue Settled: Canvas={sys_tentative.tissue['CanvasWidth']}, Sidebar={sys_tentative.tissue['SidebarWidth']}, Main={sys_tentative.tissue['MainWidth']}")
            print(f"  ✓ {GREEN}{target['name']} FITS! Choosing 'Commit'{RESET}")
            sys, chosen = decide_branch(
                sys,
                "Sidebar",
                footprint=footprint,
                decision_fn=lambda _: "Commit"
            )
            # Commit exact width
            sys = inject_constraint(sys, "SidebarWidth", Interval.exact(target["commit"]))
            sys, _ = settle_tissue(sys)

            sys, msg_commit = send_message(sys, "Sidebar", "Main", "Accept", payload=target["commit"])
            sys = follow_branch(sys, "Main", "Sidebar", "Commit")
            sys = receive_message(sys, "Main", msg_commit)
            final_mode = target["name"]
            break
        else:
            # Doesn't fit! Loop back via Retry
            conflict_msg = res.conflict if hasattr(res, "conflict") else "Insufficient space"
            print(f"  ✗ {YELLOW}{target['name']} does not fit ({conflict_msg}). Choosing 'Retry' counter-offer...{RESET}")
            sys, chosen = decide_branch(
                sys,
                "Sidebar",
                footprint=footprint,
                decision_fn=lambda _: "Retry"
            )
            sys, msg_retry = send_message(sys, "Sidebar", "Main", "CounterOffer", payload="trying_smaller")
            sys = follow_branch(sys, "Main", "Sidebar", "Retry")
            sys = receive_message(sys, "Main", msg_retry)
            attempt += 1

    print(f"\n{GREEN}▶ Protocol Successfully Terminated: {sys.is_all_terminated()}{RESET}")
    render_ascii_layout(canvas_width, sys.tissue["SidebarWidth"].lo, sys.tissue["MainWidth"].lo, final_mode)


def run_spatial_bump_demo():
    print(f"\n{BOLD}{CYAN}{'═' * 70}{RESET}")
    print(f"{BOLD}{CYAN}  SCENARIO 2: 3-Card Spatial Bump & Zero-Drift Pinning{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 70}{RESET}\n")

    print(f"Initial Canvas Positions:")
    print(f"  Card A (User is dragging rightward): x = 100px (width: 100px)")
    print(f"  Card B (Resting in the path)       : x = 150px (width: 100px)")
    print(f"  Card C (Pinned on the right edge)  : x = 600px (width: 100px) [PINNED]\n")

    # Initial tissue: Card A is dragged to 100px
    tissue = {
        "CardA": Interval.exact(100.0),
        "CardB": Interval(150.0, 400.0),
        "CardC": Interval.exact(600.0),
    }

    # Card A has width 100px + gap 20px -> Card B must be at least 100 + 100 + 20 = 220px!
    props = [
        separation_constraint("CardA", "CardB", width=100.0, gap=20.0),
        pin_constraint("CardC", 600.0),
    ]

    print(f"{BOLD}{YELLOW}▶ Applying Monotonic Spatial Propagation:{RESET}")
    result = settle(tissue, props)
    assert isinstance(result, SolveSuccess)

    print(f"  ✓ Fixed-point reached in {result.steps} steps!")
    print(f"  • Card A (Dragged) : {result.tissue['CardA']}")
    print(f"  • Card B (Displaced): {BOLD}{GREEN}{result.tissue['CardB']}{RESET} (Slid from 150px -> 220px to prevent overlap!)")
    print(f"  • Card C (Pinned)   : {BOLD}{CYAN}{result.tissue['CardC']}{RESET} (Zero drift! Perfectly stationary at 600px)\n")

    print(f"{BOLD}Canvas Visual Map:{RESET}")
    print(" [Card A: 100px]──(bump)──>[Card B: 220px] ---------------- [Card C: 600px (pinned)]\n")


def main():
    print_banner()

    # 1. Desktop: Full mode fits in round 1
    run_recursive_negotiation_demo("Desktop Viewport", canvas_width=720.0)

    # 2. Tablet: Full mode rejected, loops to round 2, compact mode fits
    run_recursive_negotiation_demo("Tablet Viewport", canvas_width=520.0)

    # 3. Spatial bump test
    run_spatial_bump_demo()


if __name__ == "__main__":
    main()
