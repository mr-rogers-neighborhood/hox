"""Property and boundary tests for Hox v2: Confluence, Footprints, Scoped Recursion, and Safety Valves."""

import unittest
from hox.session import (
    Global,
    SendG,
    ChoiceG,
    RecG,
    VarG,
    EndG,
    RecL,
    VarL,
    EndL,
    project,
)
from hox.propagator import (
    Interval,
    merge,
    sum_constraint,
    separation_constraint,
    pin_constraint,
    settle,
    SolveSuccess,
    SolveInconsistent,
)
from hox.bridge import (
    HoxState,
    project_tissue,
    decide_branch,
)


class TestV2Properties(unittest.TestCase):
    def test_confluence_under_merge(self):
        """CRDT property: settle(merge(T1, T2)) == merge(settle(T1), settle(T2))."""
        # Relation: A + B = C
        props = [sum_constraint("A", "B", "C")]

        # Replica 1 learns A is in [100, 200], C is in [400, 600]
        tissue_rep1 = {
            "A": Interval(100, 200),
            "B": Interval.unconstrained(),
            "C": Interval(400, 600),
        }
        # Replica 2 concurrently learns B is in [250, 350]
        tissue_rep2 = {
            "A": Interval.unconstrained(),
            "B": Interval(250, 350),
            "C": Interval.unconstrained(),
        }

        # Path 1: Settle both replicas locally, then merge, then settle merged
        res1 = settle(tissue_rep1, props)
        res2 = settle(tissue_rep2, props)
        self.assertIsInstance(res1, SolveSuccess)
        self.assertIsInstance(res2, SolveSuccess)
        assert isinstance(res1, SolveSuccess) and isinstance(res2, SolveSuccess)

        merged_settled = {
            k: merge(res1.tissue[k], res2.tissue[k]) for k in ["A", "B", "C"]
        }
        final_path1 = settle(merged_settled, props)

        # Path 2: Merge initial states first, then settle
        merged_initial = {
            k: merge(tissue_rep1[k], tissue_rep2[k]) for k in ["A", "B", "C"]
        }
        final_path2 = settle(merged_initial, props)

        # Confluence assertion: both paths reach the exact same fixed point!
        self.assertIsInstance(final_path1, SolveSuccess)
        self.assertIsInstance(final_path2, SolveSuccess)
        assert isinstance(final_path1, SolveSuccess) and isinstance(final_path2, SolveSuccess)

        for k in ["A", "B", "C"]:
            self.assertEqual(final_path1.tissue[k], final_path2.tissue[k])

        # Exact values:
        # A in [100, 200], B in [250, 350] -> C = A + B in [350, 550]
        # Intersect with C in [400, 600] -> C in [400, 550]
        self.assertEqual(final_path1.tissue["C"], Interval(400, 550))

    def test_non_participating_role_in_loop(self):
        """A role not involved in a loop must project to EndL, not dangling VarL."""
        proto = RecG(
            tag="Negotiate",
            body=ChoiceG(
                decider="Alice",
                branches={
                    "Retry": VarG("Negotiate"),
                    "Done": SendG("Alice", "Bob", "Finish", EndG()),
                }
            )
        )
        # Charlie is completely uninvolved in this protocol
        charlie_l = project(proto, "Charlie")
        self.assertEqual(charlie_l, EndL())

        # Alice is the decider and loops
        alice_l = project(proto, "Alice")
        self.assertIsInstance(alice_l, RecL)
        self.assertEqual(alice_l.tag, "Negotiate")

    def test_safety_valve_inconsistent_constraints(self):
        """Conflicting constraints must return SolveInconsistent without crashing or hanging."""
        state = {
            "CardA": Interval.exact(100.0),
            "CardB": Interval.exact(150.0),
        }
        # Separation demands CardB >= CardA + 100px (150 >= 200 is impossible)
        props = [
            pin_constraint("CardA", 100.0),
            pin_constraint("CardB", 150.0),
            separation_constraint("CardA", "CardB", width=100.0, gap=0.0)
        ]
        result = settle(state, props)
        self.assertIsInstance(result, SolveInconsistent)

    def test_zero_drift_spatial_bump(self):
        """Card A bumps into Card B; Card C remains completely pinned with zero drift."""
        state = {
            "CardA": Interval.exact(100.0),       # Dragged to 100px
            "CardB": Interval(120.0, 300.0),      # Starts at 120px
            "CardC": Interval.exact(500.0),       # Far away card at 500px
        }
        # Card A has width 80px + gap 10px -> demands CardB >= 100 + 80 + 10 = 190px
        props = [
            separation_constraint("CardA", "CardB", width=80.0, gap=10.0),
            pin_constraint("CardC", 500.0),
        ]
        result = settle(state, props)
        self.assertIsInstance(result, SolveSuccess)
        assert isinstance(result, SolveSuccess)

        # Card B was pushed from [120, 300] to [190, 300]
        self.assertEqual(result.tissue["CardB"].lo, 190.0)

        # Card C experienced zero drift: exactly [500, 500]
        self.assertEqual(result.tissue["CardC"], Interval.exact(500.0))

    def test_footprint_privacy_unrepresentable_snooping(self):
        """Decider cannot snoop on foreign cells; non-footprint cells do not exist in view."""
        sys = HoxState(
            endpoints={"Sidebar": EndL()},
            tissue={
                "SidebarWidth": Interval(0, 300),
                "SecretMainText": Interval(999, 999),
            }
        )

        seen_keys = []
        def my_predicate(local_view):
            seen_keys.extend(local_view.keys())
            # Attempting to access non-footprint cell raises KeyError
            with self.assertRaises(KeyError):
                _ = local_view["SecretMainText"]
            return "Done"

        project_view = project_tissue(sys.tissue, frozenset(["SidebarWidth"]))
        my_predicate(project_view)
        self.assertEqual(seen_keys, ["SidebarWidth"])


if __name__ == "__main__":
    unittest.main()

