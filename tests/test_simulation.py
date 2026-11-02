"""
Tests for NFA and DFA simulation.
"""
import pytest
from automata.nfa import NFA, EPSILON
from automata.conversion import nfa_to_dfa
from automata.simulation import simulate_nfa, simulate_dfa, NFASimResult, DFASimResult


@pytest.fixture
def nfa_accepts_a_star_b():
    """NFA accepting a*b: any number of 'a' followed by one 'b'."""
    nfa = NFA(
        states={"q0", "q1"},
        alphabet={"a", "b"},
        initial_state="q0",
        final_states={"q1"},
    )
    nfa.add_transition("q0", "a", {"q0"})
    nfa.add_transition("q0", "b", {"q1"})
    return nfa


class TestSimulationResults:
    def test_nfa_sim_result_type(self, nfa_accepts_a_star_b):
        result = simulate_nfa(nfa_accepts_a_star_b, "aab")
        assert isinstance(result, NFASimResult)

    def test_dfa_sim_result_type(self, nfa_accepts_a_star_b):
        dfa = nfa_to_dfa(nfa_accepts_a_star_b).dfa
        result = simulate_dfa(dfa, "aab")
        assert isinstance(result, DFASimResult)

    def test_nfa_accepts_a_star_b(self, nfa_accepts_a_star_b):
        assert simulate_nfa(nfa_accepts_a_star_b, "b").accepted
        assert simulate_nfa(nfa_accepts_a_star_b, "ab").accepted
        assert simulate_nfa(nfa_accepts_a_star_b, "aab").accepted
        assert simulate_nfa(nfa_accepts_a_star_b, "aaab").accepted

    def test_nfa_rejects_no_b(self, nfa_accepts_a_star_b):
        assert not simulate_nfa(nfa_accepts_a_star_b, "").accepted
        assert not simulate_nfa(nfa_accepts_a_star_b, "a").accepted
        assert not simulate_nfa(nfa_accepts_a_star_b, "aa").accepted

    def test_dfa_accepts_a_star_b(self, nfa_accepts_a_star_b):
        dfa = nfa_to_dfa(nfa_accepts_a_star_b).dfa
        assert simulate_dfa(dfa, "b").accepted
        assert simulate_dfa(dfa, "ab").accepted
        assert simulate_dfa(dfa, "aab").accepted

    def test_dfa_rejects_no_b(self, nfa_accepts_a_star_b):
        dfa = nfa_to_dfa(nfa_accepts_a_star_b).dfa
        assert not simulate_dfa(dfa, "").accepted
        assert not simulate_dfa(dfa, "a").accepted

    def test_final_states_property_nfa(self, nfa_accepts_a_star_b):
        result = simulate_nfa(nfa_accepts_a_star_b, "ab")
        assert "q1" in result.final_states

    def test_final_state_property_dfa(self, nfa_accepts_a_star_b):
        dfa = nfa_to_dfa(nfa_accepts_a_star_b).dfa
        result = simulate_dfa(dfa, "ab")
        assert result.final_state is not None

    def test_rejection_reason_populated_on_reject(self, nfa_accepts_a_star_b):
        result = simulate_nfa(nfa_accepts_a_star_b, "a")
        assert not result.accepted
        assert result.rejection_reason != ""
