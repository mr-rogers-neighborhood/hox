"""Unit tests for the functional session types (ADTs, projection, and pure state transitions)."""

import unittest
from hox.session import (
    SendG,
    ChoiceG,
    EndG,
    SendL,
    RecvL,
    InternalChoiceL,
    ExternalChoiceL,
    EndL,
    Message,
    project,
    extract_roles,
    step_send,
    step_receive,
    step_choose,
    step_follow_choice,
    ProtocolViolationError,
)


class TestFunctionalSession(unittest.TestCase):
    def setUp(self):
        # 3-party layout choreography
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

    def test_extract_roles(self):
        roles = extract_roles(self.proto)
        self.assertEqual(roles, ["Canvas", "Main", "Sidebar"])

    def test_projections(self):
        canvas_l = project(self.proto, "Canvas")
        sidebar_l = project(self.proto, "Sidebar")
        main_l = project(self.proto, "Main")

        # Canvas: !Sidebar<Init> . !Main<Init> . end
        self.assertEqual(canvas_l, SendL("Sidebar", "Init", SendL("Main", "Init", EndL())))

        # Sidebar: ?Canvas<Init> . ⊕ { Fit: !Main<AcceptFit> . end, Collapse: !Main<DoCollapse> . end }
        self.assertIsInstance(sidebar_l, RecvL)
        self.assertEqual(sidebar_l.from_role, "Canvas")
        self.assertIsInstance(sidebar_l.cont, InternalChoiceL)

        # Main: ?Canvas<Init> . &(Sidebar) { Fit: ?Sidebar<AcceptFit> . end, Collapse: ?Sidebar<DoCollapse> . end }
        self.assertIsInstance(main_l, RecvL)
        self.assertEqual(main_l.from_role, "Canvas")
        self.assertIsInstance(main_l.cont, ExternalChoiceL)

    def test_pure_transition_execution(self):
        alice_st = SendL("Bob", "Hello", EndL())
        bob_st = RecvL("Alice", "Hello", EndL())

        # Alice sends Hello
        next_alice, msg, env_a = step_send(alice_st, "Alice", "Bob", "Hello", payload=123)
        self.assertEqual(next_alice, EndL())
        self.assertEqual(msg, Message("Alice", "Bob", "Hello", 123))

        # Bob receives Hello
        next_bob, env_b = step_receive(bob_st, "Bob", msg)
        self.assertEqual(next_bob, EndL())

    def test_protocol_violation(self):
        st = SendL("Bob", "Ping", EndL())
        with self.assertRaises(ProtocolViolationError):
            step_send(st, "Alice", "Bob", "WrongLabel")


if __name__ == "__main__":
    unittest.main()
