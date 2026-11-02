"""
Tests specifically focused on NFA construction and data model.
"""
import pytest
from automata.nfa import NFA, EPSILON


class TestNFADataModel:
    def test_add_and_get_transition(self):
        nfa = NFA(states={"q0", "q1"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", "a", {"q1"})
        assert nfa.get_transitions("q0", "a") == {"q1"}

    def test_add_merges_destinations(self):
        nfa = NFA(states={"q0", "q1", "q2"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", "a", {"q1"})
        nfa.add_transition("q0", "a", {"q2"})
        assert nfa.get_transitions("q0", "a") == {"q1", "q2"}

    def test_epsilon_transition_stored(self):
        nfa = NFA(states={"q0", "q1"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", EPSILON, {"q1"})
        assert nfa.has_epsilon_transitions()

    def test_no_epsilon_transitions(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", "a", {"q0"})
        assert not nfa.has_epsilon_transitions()

    def test_from_dict_roundtrip(self):
        data = {
            "states": ["q0", "q1"],
            "alphabet": ["a"],
            "initial_state": "q0",
            "final_states": ["q1"],
            "transitions": {"q0": {"a": ["q1"]}},
        }
        nfa = NFA.from_dict(data)
        assert nfa.states == {"q0", "q1"}
        assert nfa.initial_state == "q0"
        assert "q1" in nfa.final_states
        assert "q1" in nfa.get_transitions("q0", "a")

    def test_to_dict_serializes(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q0", final_states={"q0"})
        nfa.add_transition("q0", "a", {"q0"})
        d = nfa.to_dict()
        assert "states" in d
        assert "transitions" in d

    def test_get_transitions_missing(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q0", final_states=set())
        # No transition defined
        assert nfa.get_transitions("q0", "a") == set()
        assert nfa.get_transitions("q_missing", "a") == set()

    def test_reachable_states(self):
        nfa = NFA(states={"q0", "q1", "q2"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", "a", {"q1"})
        # q2 is not reachable
        reachable = nfa.reachable_states()
        assert "q0" in reachable
        assert "q1" in reachable
        assert "q2" not in reachable
