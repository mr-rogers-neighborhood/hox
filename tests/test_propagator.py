"""Unit tests for the pure functional propagator engine."""

import unittest
from hox.propagator import (
    Interval,
    ContradictionError,
    merge,
    plus,
    minus,
    sum_constraint,
    inject,
    settle,
    SolveSuccess,
    SolveInconsistent,
)


class TestFunctionalLattice(unittest.TestCase):
    def test_merge_narrowing(self):
        i1 = Interval(100, 500)
        i2 = Interval(200, 600)
        merged = merge(i1, i2)
        self.assertEqual(merged.lo, 200)
        self.assertEqual(merged.hi, 500)

    def test_contradiction_detection(self):
        i1 = Interval(100, 200)
        i2 = Interval(300, 400)
        with self.assertRaises(ContradictionError):
            merge(i1, i2)

    def test_interval_arithmetic(self):
        i1 = Interval(10, 20)
        i2 = Interval(5, 15)
        self.assertEqual((plus(i1, i2).lo, plus(i1, i2).hi), (15, 35))
        self.assertEqual((minus(i1, i2).lo, minus(i1, i2).hi), (-5, 15))


class TestFunctionalPropagatorEngine(unittest.TestCase):
    def test_multi_directional_sum_forward(self):
        # A=200, B=300 -> deduce C=500
        state = {
            "A": Interval.exact(200),
            "B": Interval.exact(300),
            "C": Interval.unconstrained(),
        }
        props = [sum_constraint("A", "B", "C")]
        res = settle(state, props)

        self.assertIsInstance(res, SolveSuccess)
        assert isinstance(res, SolveSuccess)
        self.assertEqual(res.tissue["C"].lo, 500)
        self.assertEqual(res.tissue["C"].hi, 500)

    def test_backward_deduction(self):
        # C=400, B=150 -> deduce A=250
        state = {
            "A": Interval.unconstrained(),
            "B": Interval.exact(150),
            "C": Interval.exact(400),
        }
        props = [sum_constraint("A", "B", "C")]
        res = settle(state, props)

        self.assertIsInstance(res, SolveSuccess)
        assert isinstance(res, SolveSuccess)
        self.assertEqual(res.tissue["A"].lo, 250)
        self.assertEqual(res.tissue["A"].hi, 250)

    def test_interval_relaxation_and_quiescence(self):
        # A in [200, 350], B >= 400, C == 700
        state = {
            "Sidebar": Interval(200, 350),
            "Main": Interval.at_least(400),
            "Canvas": Interval.exact(700),
        }
        props = [sum_constraint("Sidebar", "Main", "Canvas")]
        res = settle(state, props)

        self.assertIsInstance(res, SolveSuccess)
        assert isinstance(res, SolveSuccess)
        self.assertEqual(res.tissue["Sidebar"].lo, 200)
        self.assertEqual(res.tissue["Sidebar"].hi, 300)
        self.assertEqual(res.tissue["Main"].lo, 400)
        self.assertEqual(res.tissue["Main"].hi, 500)


if __name__ == "__main__":
    unittest.main()
