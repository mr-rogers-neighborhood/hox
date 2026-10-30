"""Integration tests for the pure functional Hox bridge."""

import unittest
from hox.session import SendG, ChoiceG, EndG, project
from hox.propagator import Interval, sum_constraint, SolveSuccess
from hox.bridge import (
    HoxState,
    inject_constraint,
    settle_tissue,
    send_message,
    receive_message,
    decide_branch,
    follow_branch,
)


class TestFunctionalHoxBridge(unittest.TestCase):
    def setUp(self):
        self.proto = SendG(
            sender="Canvas",
            receiver="Sidebar",
            label="Init",
            cont=SendG(
                sender="Canvas",
                receiver="Main",
                label="Init",
                cont=ChoiceG(
                    decider="Sidebar",
                    branches={
                        "Fit": SendG("Sidebar", "Main", "AcceptFit", EndG()),
                        "Collapse": SendG("Sidebar", "Main", "DoCollapse", EndG()),
                    }
                )
            )
        )

    def _init_system(self, canvas_width: float) -> HoxState:
        endpoints = {
            "Canvas": project(self.proto, "Canvas"),
            "Sidebar": project(self.proto, "Sidebar"),
            "Main": project(self.proto, "Main"),
        }
        tissue = {
            "CanvasWidth": Interval.exact(canvas_width),
            "SidebarWidth": Interval.unconstrained(),
            "MainWidth": Interval.unconstrained(),
        }
        props = [sum_constraint("SidebarWidth", "MainWidth", "CanvasWidth")]
        return HoxState(endpoints=endpoints, tissue=tissue, propagators=props)

    def test_wide_screen_branch_fit(self):
        sys0 = self._init_system(700.0)

        # 1. Canvas sends Init to Sidebar and Main
        sys1, msg1 = send_message(sys0, "Canvas", "Sidebar", "Init", payload=700.0)
        sys2, msg2 = send_message(sys1, "Canvas", "Main", "Init", payload=700.0)

        # 2. Sidebar & Main receive Init and inject elastic desires into the tissue
        sys3 = receive_message(sys2, "Sidebar", msg1)
        sys4 = inject_constraint(sys3, "SidebarWidth", Interval(0.0, 350.0))

        sys5 = receive_message(sys4, "Main", msg2)
        sys6 = inject_constraint(sys5, "MainWidth", Interval.at_least(400.0))

        # 3. Pure fixed point settlement (Quiescence)
        sys7, res = settle_tissue(sys6)
        self.assertIsInstance(res, SolveSuccess)
        assert isinstance(res, SolveSuccess)
        self.assertGreater(res.steps, 0)

        # Settled: Canvas=700, Main>=400 -> Sidebar in [0, 300]
        self.assertEqual(sys7.tissue["SidebarWidth"].hi, 300.0)

        # 4. Sidebar decides branch using its declared footprint
        sys8, chosen = decide_branch(
            sys7,
            "Sidebar",
            footprint=frozenset(["SidebarWidth"]),
            decision_fn=lambda local_view: "Fit" if local_view["SidebarWidth"].hi >= 200.0 else "Collapse"
        )
        self.assertEqual(chosen, "Fit")

        # Sidebar commits to width 250 and notifies Main
        sys9 = inject_constraint(sys8, "SidebarWidth", Interval.exact(250.0))
        sys10, _ = settle_tissue(sys9)
        sys11, msg_choice = send_message(sys10, "Sidebar", "Main", "AcceptFit", payload=250.0)

        # 5. Main follows external choice and receives message
        sys12 = follow_branch(sys11, "Main", "Sidebar", "Fit")
        sys13 = receive_message(sys12, "Main", msg_choice)

        # Verification: all terminated, Main got 450px
        self.assertTrue(sys13.is_all_terminated())
        self.assertEqual(sys13.tissue["MainWidth"].lo, 450.0)
        self.assertEqual(sys13.tissue["MainWidth"].hi, 450.0)

    def test_narrow_screen_branch_collapse(self):
        sys0 = self._init_system(450.0)

        # Canvas sends Init
        sys1, msg1 = send_message(sys0, "Canvas", "Sidebar", "Init", payload=450.0)
        sys2, msg2 = send_message(sys1, "Canvas", "Main", "Init", payload=450.0)

        # Receive & inject constraints
        sys3 = receive_message(sys2, "Sidebar", msg1)
        sys4 = inject_constraint(sys3, "SidebarWidth", Interval(0.0, 350.0))
        sys5 = receive_message(sys4, "Main", msg2)
        sys6 = inject_constraint(sys5, "MainWidth", Interval.at_least(400.0))

        # Settle
        sys7, res = settle_tissue(sys6)
        self.assertIsInstance(res, SolveSuccess)
        # Canvas=450, Main>=400 -> Sidebar max is 50px (< 200px)
        self.assertEqual(sys7.tissue["SidebarWidth"].hi, 50.0)

        # Sidebar decides branch: space < 200 -> Collapse!
        sys8, chosen = decide_branch(
            sys7,
            "Sidebar",
            footprint=frozenset(["SidebarWidth"]),
            decision_fn=lambda local_view: "Fit" if local_view["SidebarWidth"].hi >= 200.0 else "Collapse"
        )
        self.assertEqual(chosen, "Collapse")

        # Sidebar collapses to 0
        sys9 = inject_constraint(sys8, "SidebarWidth", Interval.exact(0.0))
        sys10, _ = settle_tissue(sys9)
        sys11, msg_collapse = send_message(sys10, "Sidebar", "Main", "DoCollapse", payload=0.0)

        # Main follows
        sys12 = follow_branch(sys11, "Main", "Sidebar", "Collapse")
        sys13 = receive_message(sys12, "Main", msg_collapse)

        # Verification: Main gets entire 450px
        self.assertTrue(sys13.is_all_terminated())
        self.assertEqual(sys13.tissue["MainWidth"].lo, 450.0)
        self.assertEqual(sys13.tissue["MainWidth"].hi, 450.0)


if __name__ == "__main__":
    unittest.main()
