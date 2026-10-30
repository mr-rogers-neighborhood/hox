"""Hox Functional Demo: Pure Functional Session Projections over Propagator Networks.

Demonstrates 3-party layout negotiation (Canvas, Sidebar, MainContent):
- All data structures are immutable dataclasses (ADTs).
- Propagators are pure state transformers: State -> State.
- Quiescence is a pure fixed-point loop: fix(F).
- Session projection and transitions are pure pattern-matching functions.
"""

from __future__ import annotations
from hox.session import (
    SendG,
    ChoiceG,
    EndG,
    project,
    extract_roles,
)
from hox.propagator import Interval, sum_constraint
from hox.bridge import (
    HoxState,
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
RESET = "\033[0m"


def print_header(title: str):
    print(f"\n{BOLD}{CYAN}{'═' * 70}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 70}{RESET}\n")


def print_step(num: int, title: str):
    print(f"{BOLD}{YELLOW}▶ Step {num}: {title}{RESET}")


def render_ascii_layout(canvas_w: float, sidebar_w: float, main_w: float):
    total_cols = 50
    scale = total_cols / canvas_w if canvas_w > 0 else 1
    s_cols = int(round(sidebar_w * scale))
    m_cols = total_cols - s_cols

    print(f"\n{BOLD}Layout Render ({canvas_w:g}px Total):{RESET}")
    print("┌" + "─" * s_cols + "┬" + "─" * m_cols + "┐")
    s_label = f"Nav({sidebar_w:g}px)"[:s_cols].center(s_cols) if s_cols > 0 else ""
    m_label = f"Main Reading Area ({main_w:g}px)"[:m_cols].center(m_cols)
    print(f"│{s_label}│{m_label}│")
    print("└" + "─" * s_cols + "┴" + "─" * m_cols + "┘\n")


def run_scenario(scenario_name: str, canvas_width: float):
    print_header(f"SCENARIO: {scenario_name} (Canvas = {canvas_width}px)")

    # 1. Pure Choreographic Global Type (ADTs)
    print_step(1, "The Hox Gene (Pure Global Choreography ADT)")
    protocol = SendG(
        sender="Canvas",
        receiver="Sidebar",
        label="InitBounds",
        cont=SendG(
            sender="Canvas",
            receiver="Main",
            label="InitBounds",
            cont=ChoiceG(
                decider="Sidebar",
                branches={
                    "Fit": SendG("Sidebar", "Main", "AcceptFit", EndG()),
                    "Collapse": SendG("Sidebar", "Main", "DoCollapse", EndG()),
                }
            )
        )
    )
    print(f"  Choreography : {protocol}")
    print(f"  Roles        : {', '.join(extract_roles(protocol))}\n")

    # 2. Pure Recursive Projection into Local Types
    print_step(2, "Pure Recursive Projection: Global -> Local Endpoints")
    canvas_local = project(protocol, "Canvas")
    sidebar_local = project(protocol, "Sidebar")
    main_local = project(protocol, "Main")

    print(f"  {MAGENTA}Canvas  Local:{RESET} {canvas_local}")
    print(f"  {MAGENTA}Sidebar Local:{RESET} {sidebar_local}")
    print(f"  {MAGENTA}Main    Local:{RESET} {main_local}\n")

    # 3. Initialize Immutable Hybrid System State
    print_step(3, "Initializing Immutable System State (HoxState)")
    endpoints = {
        "Canvas": canvas_local,
        "Sidebar": sidebar_local,
        "Main": main_local,
    }
    tissue = {
        "CanvasWidth": Interval.exact(canvas_width),
        "SidebarWidth": Interval.unconstrained(),
        "MainWidth": Interval.unconstrained(),
    }
    # Propagators as pure functions: State -> State
    propagators = [sum_constraint("SidebarWidth", "MainWidth", "CanvasWidth")]

    sys0 = HoxState(endpoints=endpoints, tissue=tissue, propagators=propagators)
    print(f"  Attached Propagator: sum_constraint(SidebarWidth + MainWidth = CanvasWidth)")
    print(f"  Initial State: CanvasWidth = {sys0.tissue['CanvasWidth']}\n")

    # 4. Canvas Sends InitBounds to Sidebar and Main
    print_step(4, "Pure Session Stepping: Canvas broadcasts InitBounds")
    sys1, msg1 = send_message(sys0, "Canvas", "Sidebar", "InitBounds", payload=canvas_width)
    sys2, msg2 = send_message(sys1, "Canvas", "Main", "InitBounds", payload=canvas_width)
    print(f"  {GREEN}{msg1}{RESET}")
    print(f"  {GREEN}{msg2}{RESET}")

    # 5. Endpoints receive and inject elastic constraints into tissue
    print_step(5, "Endpoints consume messages and inject elastic constraints")
    sys3 = receive_message(sys2, "Sidebar", msg1)
    sys4 = inject_constraint(sys3, "SidebarWidth", Interval(0.0, 350.0))

    sys5 = receive_message(sys4, "Main", msg2)
    sys6 = inject_constraint(sys5, "MainWidth", Interval.at_least(400.0))
    print(f"  Sidebar injected elastic desire: [0, 350]px")
    print(f"  Main injected legibility floor : >= 400px\n")

    # 6. Settle Propagator Tissue to Fixed Point (Quiescence)
    print_step(6, "Pure Fixed-Point Computation: settle_tissue(sys6)")
    sys7, steps = settle_tissue(sys6)
    print(f"  ✓ {GREEN}Quiescence reached in {steps} functional relaxation steps!{RESET}")
    for cell_name, val in sys7.tissue.items():
        print(f"    • {cell_name:14}: {BOLD}{val}{RESET}")
    print()

    # 7. Branch Decision via Settled Interval
    print_step(7, "Pure Branch Evaluation from Settled Lattice Values")
    # Sidebar requires at least 200px to be viable
    sidebar_interval = sys7.tissue["SidebarWidth"]
    can_fit = sidebar_interval.hi >= 200.0

    if can_fit:
        sys8, chosen_branch = decide_branch(
            sys7,
            "Sidebar",
            lambda tissue: "Fit" if tissue["SidebarWidth"].hi >= 200.0 else "Collapse"
        )
        print(f"  Decision : Sidebar width {sidebar_interval.hi:g}px >= 200px -> Branch '{chosen_branch}'")
        
        # Commit chosen width and settle
        actual_sidebar = min(sidebar_interval.hi, 250.0)
        sys9 = inject_constraint(sys8, "SidebarWidth", Interval.exact(actual_sidebar))
        sys10, _ = settle_tissue(sys9)

        # Notify Main
        sys11, msg_choice = send_message(sys10, "Sidebar", "Main", "AcceptFit", payload=actual_sidebar)
        print(f"  {GREEN}{msg_choice}{RESET}")

        sys12 = follow_branch(sys11, "Main", "Sidebar", "Fit")
        sys_final = receive_message(sys12, "Main", msg_choice)
    else:
        sys8, chosen_branch = decide_branch(
            sys7,
            "Sidebar",
            lambda tissue: "Fit" if tissue["SidebarWidth"].hi >= 200.0 else "Collapse"
        )
        print(f"  Decision : Sidebar max width {sidebar_interval.hi:g}px < 200px -> Branch '{chosen_branch}'")

        # Collapse sidebar to 0 and settle
        sys9 = inject_constraint(sys8, "SidebarWidth", Interval.exact(0.0))
        sys10, _ = settle_tissue(sys9)

        # Notify Main
        sys11, msg_choice = send_message(sys10, "Sidebar", "Main", "DoCollapse", payload=0.0)
        print(f"  {GREEN}{msg_choice}{RESET}")

        sys12 = follow_branch(sys11, "Main", "Sidebar", "Collapse")
        sys_final = receive_message(sys12, "Main", msg_choice)

    # 8. Protocol Completion & Visual Render
    print_step(8, "Protocol Completion Verification")
    print(f"  All Roles Terminated: {sys_final.is_all_terminated()}")
    final_sidebar = sys_final.tissue["SidebarWidth"].lo
    final_main = sys_final.tissue["MainWidth"].lo
    print(f"  Final Widths -> Sidebar: {final_sidebar:g}px, Main: {final_main:g}px")
    render_ascii_layout(canvas_width, final_sidebar, final_main)


def main():
    print(f"{BOLD}{MAGENTA}")
    print("  _   _  _____  __   __")
    print(" | | | |/ _ \\ \\/ /  ")
    print(" | |_| | | | >  <   Functional Session Projections")
    print(" |  _  | |_| / /\\ \\  over Sussman Propagator Networks")
    print(" |_| |_|\\___/_/  \\_\\")
    print(f"{RESET}")

    # Wide viewport scenario
    run_scenario("Wide Desktop Viewport", canvas_width=720.0)

    # Narrow viewport scenario
    run_scenario("Narrow / Split-Screen Viewport", canvas_width=480.0)


if __name__ == "__main__":
    main()
