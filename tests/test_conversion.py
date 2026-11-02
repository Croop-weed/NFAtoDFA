"""
Comprehensive pytest test suite for the NFA → DFA Simulator.

Tests cover:
- epsilon_closure() correctness
- move() correctness
- Basic NFA to DFA conversion
- Multiple transitions for one symbol
- Epsilon transitions during conversion
- Empty / dead state generation
- Acceptance of valid strings
- Rejection of invalid strings
- Empty string (ε) acceptance
- Arbitrary state names
- NFA ↔ DFA equivalence for multiple strings
"""

from __future__ import annotations

import itertools
import pytest

from automata.nfa import NFA, EPSILON
from automata.dfa import DFA
from automata.conversion import nfa_to_dfa, epsilon_closure, move, ConversionResult
from automata.simulation import simulate_nfa, simulate_dfa
from automata.validation import validate_automaton
from examples.sample_nfas import get_example, EXAMPLES


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def nfa_ending_ba() -> NFA:
    """NFA accepting strings over {a, b} ending in 'ba'."""
    return get_example("Strings ending in 'ba'")


@pytest.fixture
def nfa_containing_abb() -> NFA:
    """NFA accepting strings over {a, b} containing 'abb'."""
    return get_example("Strings containing 'abb'")


@pytest.fixture
def nfa_epsilon() -> NFA:
    """NFA with ε-transitions: 2nd-to-last symbol is '1'."""
    return get_example("ε-transitions: second-to-last is 1")


@pytest.fixture
def nfa_ending_01() -> NFA:
    """NFA accepting binary strings ending in '01'."""
    return get_example("Strings ending in '01'")


@pytest.fixture
def nfa_simple() -> NFA:
    """
    Simple hand-crafted NFA:
      States: {A, B, C}
      Alphabet: {0, 1}
      A --0--> {A, B}
      A --1--> {A}
      B --1--> {C}
      Accepts strings over {0,1} ending in '01'.
    """
    nfa = NFA(
        states={"A", "B", "C"},
        alphabet={"0", "1"},
        initial_state="A",
        final_states={"C"},
    )
    nfa.add_transition("A", "0", {"A", "B"})
    nfa.add_transition("A", "1", {"A"})
    nfa.add_transition("B", "1", {"C"})
    return nfa


@pytest.fixture
def nfa_arbitrary_names() -> NFA:
    """NFA with unusual/arbitrary state names."""
    nfa = NFA(
        states={"start", "middle", "end_state"},
        alphabet={"x", "y"},
        initial_state="start",
        final_states={"end_state"},
    )
    nfa.add_transition("start", "x", {"start", "middle"})
    nfa.add_transition("start", "y", {"start"})
    nfa.add_transition("middle", "y", {"end_state"})
    return nfa


@pytest.fixture
def nfa_with_dead_state() -> NFA:
    """NFA where some (state, symbol) combinations lead nowhere → dead state."""
    nfa = NFA(
        states={"p", "q"},
        alphabet={"a", "b"},
        initial_state="p",
        final_states={"q"},
    )
    nfa.add_transition("p", "a", {"q"})
    # p --b--> ∅  (no transition defined)
    # q has no outgoing transitions
    return nfa


@pytest.fixture
def nfa_epsilon_only_loop() -> NFA:
    """NFA where start state has ε-transition to itself and to accepting state."""
    nfa = NFA(
        states={"s0", "s1", "s2"},
        alphabet={"a"},
        initial_state="s0",
        final_states={"s2"},
    )
    nfa.add_transition("s0", EPSILON, {"s1"})
    nfa.add_transition("s1", "a", {"s2"})
    return nfa


# ─────────────────────────────────────────────────────────────────────────────
# Tests: epsilon_closure()
# ─────────────────────────────────────────────────────────────────────────────

class TestEpsilonClosure:
    def test_no_epsilon_transitions(self, nfa_simple):
        """Without ε-transitions, closure = the state itself."""
        cl = epsilon_closure({"A"}, nfa_simple.transitions)
        assert cl == frozenset({"A"})

    def test_epsilon_reaches_other_state(self, nfa_epsilon_only_loop):
        """ε-transition from s0 → s1 means ε-closure({s0}) = {s0, s1}."""
        cl = epsilon_closure({"s0"}, nfa_epsilon_only_loop.transitions)
        assert cl == frozenset({"s0", "s1"})

    def test_closure_from_multiple_seeds(self, nfa_epsilon_only_loop):
        cl = epsilon_closure({"s0", "s2"}, nfa_epsilon_only_loop.transitions)
        assert "s0" in cl and "s1" in cl and "s2" in cl

    def test_closure_of_empty_set(self, nfa_simple):
        cl = epsilon_closure(set(), nfa_simple.transitions)
        assert cl == frozenset()

    def test_closure_includes_self(self, nfa_simple):
        """Every state is in its own ε-closure (zero ε-moves)."""
        for state in nfa_simple.states:
            cl = epsilon_closure({state}, nfa_simple.transitions)
            assert state in cl

    def test_closure_transitive(self):
        """ε-closure must follow chains: a →ε→ b →ε→ c gives {a,b,c}."""
        transitions = {
            "a": {EPSILON: {"b"}},
            "b": {EPSILON: {"c"}},
        }
        cl = epsilon_closure({"a"}, transitions)
        assert cl == frozenset({"a", "b", "c"})

    def test_closure_cycle_safe(self):
        """ε-closure must terminate even with ε-cycles."""
        transitions = {
            "a": {EPSILON: {"b"}},
            "b": {EPSILON: {"a"}},   # cycle
        }
        cl = epsilon_closure({"a"}, transitions)
        assert cl == frozenset({"a", "b"})

    def test_epsilon_example_fixture(self, nfa_epsilon):
        """q0 has an ε-transition to qh, so ε-closure({q0}) = {q0, qh}."""
        cl = epsilon_closure({"q0"}, nfa_epsilon.transitions)
        assert "q0" in cl and "qh" in cl


# ─────────────────────────────────────────────────────────────────────────────
# Tests: move()
# ─────────────────────────────────────────────────────────────────────────────

class TestMove:
    def test_basic_move(self, nfa_simple):
        result = move({"A"}, "0", nfa_simple.transitions)
        assert result == frozenset({"A", "B"})

    def test_move_multiple_source_states(self, nfa_simple):
        """move({A, B}, 1) = A's targets ∪ B's targets for '1'."""
        result = move({"A", "B"}, "1", nfa_simple.transitions)
        assert "A" in result  # A --1--> A
        assert "C" in result  # B --1--> C

    def test_move_empty_set(self, nfa_simple):
        result = move(set(), "0", nfa_simple.transitions)
        assert result == frozenset()

    def test_move_no_transition(self, nfa_simple):
        """B has no '0' transition — result should be empty."""
        result = move({"B"}, "0", nfa_simple.transitions)
        assert result == frozenset()

    def test_move_does_not_follow_epsilon(self, nfa_epsilon_only_loop):
        """move() must NOT follow ε-transitions."""
        result = move({"s0"}, "a", nfa_epsilon_only_loop.transitions)
        # s0 has no 'a' transition (only ε); s1 is reached via ε, not move
        assert result == frozenset()


# ─────────────────────────────────────────────────────────────────────────────
# Tests: nfa_to_dfa() structure
# ─────────────────────────────────────────────────────────────────────────────

class TestNFAtoDFAStructure:
    def test_returns_conversion_result(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        assert isinstance(result, ConversionResult)
        assert isinstance(result.dfa, DFA)

    def test_dfa_has_initial_state(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        assert result.dfa.initial_state is not None

    def test_initial_state_is_epsilon_closure(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        expected = epsilon_closure({nfa_simple.initial_state}, nfa_simple.transitions)
        assert result.dfa.initial_state == expected

    def test_all_dfa_states_are_frozensets(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        for state in result.dfa.states:
            assert isinstance(state, frozenset)

    def test_dfa_states_are_subsets_of_nfa_states(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        for state in result.dfa.states:
            assert state.issubset(nfa_simple.states)

    def test_dfa_alphabet_matches_nfa(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        assert result.dfa.alphabet == nfa_simple.alphabet

    def test_accepting_states_contain_nfa_final(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        for state in result.dfa.final_states:
            assert state & nfa_simple.final_states  # non-empty intersection

    def test_non_accepting_states_have_no_nfa_final(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        non_final = result.dfa.states - result.dfa.final_states
        for state in non_final:
            assert not (state & nfa_simple.final_states)

    def test_steps_recorded(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        assert len(result.steps) > 0

    def test_epsilon_closures_recorded(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        for state in nfa_simple.states:
            assert state in result.epsilon_closures

    def test_multiple_transitions_same_symbol(self):
        """NFA with two outgoing 'a' transitions from the same state."""
        nfa = NFA(
            states={"p", "q", "r"},
            alphabet={"a"},
            initial_state="p",
            final_states={"r"},
        )
        nfa.add_transition("p", "a", {"q", "r"})
        result = nfa_to_dfa(nfa)
        dfa = result.dfa
        # From initial state on 'a', both q and r should be in the DFA state
        init = dfa.initial_state  # = {p}
        next_state = dfa.get_transition(init, "a")
        assert next_state is not None
        assert "q" in next_state
        assert "r" in next_state

    def test_dead_state_generated(self, nfa_with_dead_state):
        """Missing NFA transitions should produce the dead state ∅."""
        result = nfa_to_dfa(nfa_with_dead_state)
        dead = frozenset()
        assert dead in result.dfa.states

    def test_dead_state_not_accepting(self, nfa_with_dead_state):
        result = nfa_to_dfa(nfa_with_dead_state)
        dead = frozenset()
        assert dead not in result.dfa.final_states

    def test_arbitrary_state_names(self, nfa_arbitrary_names):
        """Conversion must work with any state name strings."""
        result = nfa_to_dfa(nfa_arbitrary_names)
        assert result.dfa is not None
        assert len(result.dfa.states) > 0

    def test_epsilon_transition_conversion(self, nfa_epsilon_only_loop):
        """NFA with ε-transitions should produce correct DFA."""
        result = nfa_to_dfa(nfa_epsilon_only_loop)
        dfa = result.dfa
        # Initial DFA state should include s1 (via ε from s0)
        assert "s1" in dfa.initial_state

    def test_no_duplicate_dfa_states(self, nfa_simple):
        result = nfa_to_dfa(nfa_simple)
        # frozensets in a set cannot have duplicates by definition;
        # verify the count is sane
        assert len(result.dfa.states) == len(set(result.dfa.states))


# ─────────────────────────────────────────────────────────────────────────────
# Tests: simulate_nfa()
# ─────────────────────────────────────────────────────────────────────────────

class TestSimulateNFA:
    def test_accepts_valid_string(self, nfa_ending_ba):
        assert simulate_nfa(nfa_ending_ba, "ba").accepted
        assert simulate_nfa(nfa_ending_ba, "aba").accepted
        assert simulate_nfa(nfa_ending_ba, "bba").accepted

    def test_rejects_invalid_string(self, nfa_ending_ba):
        assert not simulate_nfa(nfa_ending_ba, "ab").accepted
        assert not simulate_nfa(nfa_ending_ba, "b").accepted
        assert not simulate_nfa(nfa_ending_ba, "a").accepted

    def test_empty_string_rejection(self, nfa_ending_ba):
        """Empty string should be rejected (no final state is initial)."""
        assert not simulate_nfa(nfa_ending_ba, "").accepted

    def test_empty_string_acceptance(self):
        """NFA whose initial state is also final should accept ε."""
        nfa = NFA(
            states={"q0"},
            alphabet={"a"},
            initial_state="q0",
            final_states={"q0"},
        )
        assert simulate_nfa(nfa, "").accepted

    def test_steps_count(self, nfa_ending_ba):
        """Number of simulation steps = len(input) + 1 (initial step)."""
        result = simulate_nfa(nfa_ending_ba, "aba")
        assert len(result.steps) == len("aba") + 1

    def test_initial_step_has_none_symbol(self, nfa_ending_ba):
        result = simulate_nfa(nfa_ending_ba, "ba")
        assert result.steps[0].symbol is None

    def test_invalid_symbol_rejected(self, nfa_ending_ba):
        result = simulate_nfa(nfa_ending_ba, "c")
        assert not result.accepted
        assert "not in the alphabet" in result.rejection_reason

    def test_epsilon_nfa_accepts_a(self, nfa_epsilon_only_loop):
        """ε: s0 →ε→ s1, s1 →a→ s2 (final). Should accept 'a'."""
        assert simulate_nfa(nfa_epsilon_only_loop, "a").accepted

    def test_epsilon_nfa_rejects_empty(self, nfa_epsilon_only_loop):
        """s2 is only final; without 'a', we stay in {s0,s1}."""
        assert not simulate_nfa(nfa_epsilon_only_loop, "").accepted

    def test_abb_accepts(self, nfa_containing_abb):
        assert simulate_nfa(nfa_containing_abb, "abb").accepted
        assert simulate_nfa(nfa_containing_abb, "aabb").accepted
        assert simulate_nfa(nfa_containing_abb, "babb").accepted

    def test_abb_rejects(self, nfa_containing_abb):
        assert not simulate_nfa(nfa_containing_abb, "ab").accepted
        assert not simulate_nfa(nfa_containing_abb, "bba").accepted


# ─────────────────────────────────────────────────────────────────────────────
# Tests: simulate_dfa()
# ─────────────────────────────────────────────────────────────────────────────

class TestSimulateDFA:
    def test_dfa_accepts_valid(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        assert simulate_dfa(dfa, "ba").accepted
        assert simulate_dfa(dfa, "aba").accepted

    def test_dfa_rejects_invalid(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        assert not simulate_dfa(dfa, "ab").accepted
        assert not simulate_dfa(dfa, "b").accepted

    def test_dfa_empty_string_rejection(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        assert not simulate_dfa(dfa, "").accepted

    def test_dfa_steps_count(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        result = simulate_dfa(dfa, "aba")
        assert len(result.steps) == len("aba") + 1

    def test_dfa_invalid_symbol(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        result = simulate_dfa(dfa, "c")
        assert not result.accepted

    def test_dfa_initial_step_none_symbol(self, nfa_ending_ba):
        dfa = nfa_to_dfa(nfa_ending_ba).dfa
        result = simulate_dfa(dfa, "ba")
        assert result.steps[0].symbol is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests: NFA ↔ DFA equivalence
# ─────────────────────────────────────────────────────────────────────────────

def _check_equivalence(nfa: NFA, test_strings: list[str]) -> list[str]:
    """Return list of strings where NFA and DFA disagree."""
    dfa = nfa_to_dfa(nfa).dfa
    mismatches = []
    for s in test_strings:
        nfa_r = simulate_nfa(nfa, s).accepted
        dfa_r = simulate_dfa(dfa, s).accepted
        if nfa_r != dfa_r:
            mismatches.append(s)
    return mismatches


def _all_strings_up_to(alphabet: set[str], max_len: int) -> list[str]:
    """Generate all strings over alphabet up to length max_len."""
    result = [""]
    for length in range(1, max_len + 1):
        for combo in itertools.product(sorted(alphabet), repeat=length):
            result.append("".join(combo))
    return result


class TestEquivalence:
    def test_ending_ba_equivalence(self, nfa_ending_ba):
        strings = _all_strings_up_to({"a", "b"}, 5)
        mismatches = _check_equivalence(nfa_ending_ba, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_containing_abb_equivalence(self, nfa_containing_abb):
        strings = _all_strings_up_to({"a", "b"}, 6)
        mismatches = _check_equivalence(nfa_containing_abb, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_ending_01_equivalence(self, nfa_ending_01):
        strings = _all_strings_up_to({"0", "1"}, 6)
        mismatches = _check_equivalence(nfa_ending_01, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_epsilon_example_equivalence(self, nfa_epsilon):
        strings = _all_strings_up_to({"0", "1"}, 5)
        mismatches = _check_equivalence(nfa_epsilon, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_arbitrary_names_equivalence(self, nfa_arbitrary_names):
        strings = _all_strings_up_to({"x", "y"}, 5)
        mismatches = _check_equivalence(nfa_arbitrary_names, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_simple_nfa_equivalence(self, nfa_simple):
        strings = _all_strings_up_to({"0", "1"}, 6)
        mismatches = _check_equivalence(nfa_simple, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_epsilon_only_loop_equivalence(self, nfa_epsilon_only_loop):
        strings = _all_strings_up_to({"a"}, 5)
        mismatches = _check_equivalence(nfa_epsilon_only_loop, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"

    def test_dead_state_nfa_equivalence(self, nfa_with_dead_state):
        strings = _all_strings_up_to({"a", "b"}, 4)
        mismatches = _check_equivalence(nfa_with_dead_state, strings)
        assert mismatches == [], f"Mismatches on: {mismatches}"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: validation
# ─────────────────────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_nfa_passes(self, nfa_simple):
        v = validate_automaton(nfa_simple)
        assert v.is_valid

    def test_missing_initial_state(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="", final_states=set())
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_initial_state_not_in_q(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q1", final_states=set())
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_final_state_not_in_q(self):
        nfa = NFA(
            states={"q0"},
            alphabet={"a"},
            initial_state="q0",
            final_states={"q_nonexistent"},
        )
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_transition_dest_not_in_q(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q0", final_states=set())
        nfa.add_transition("q0", "a", {"q_nonexistent"})
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_epsilon_in_alphabet_rejected(self):
        nfa = NFA(
            states={"q0"},
            alphabet={"a", EPSILON},
            initial_state="q0",
            final_states=set(),
        )
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_empty_states_rejected(self):
        nfa = NFA(states=set(), alphabet={"a"}, initial_state="", final_states=set())
        v = validate_automaton(nfa)
        assert not v.is_valid

    def test_no_final_states_warning(self):
        nfa = NFA(states={"q0"}, alphabet={"a"}, initial_state="q0", final_states=set())
        v = validate_automaton(nfa)
        # Should be valid but with a warning
        assert v.is_valid
        assert any("accepting" in w.lower() for w in v.warnings)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: preloaded examples
# ─────────────────────────────────────────────────────────────────────────────

class TestPreloadedExamples:
    @pytest.mark.parametrize("example_name", list(EXAMPLES.keys()))
    def test_example_loads(self, example_name):
        nfa = get_example(example_name)
        assert isinstance(nfa, NFA)

    @pytest.mark.parametrize("example_name", list(EXAMPLES.keys()))
    def test_example_validates(self, example_name):
        nfa = get_example(example_name)
        v = validate_automaton(nfa)
        assert v.is_valid, f"Example '{example_name}' failed validation: {v.errors}"

    @pytest.mark.parametrize("example_name", list(EXAMPLES.keys()))
    def test_example_accepts_listed_strings(self, example_name):
        nfa = get_example(example_name)
        example = EXAMPLES[example_name]
        for s in example["accepts"]:
            result = simulate_nfa(nfa, s)
            assert result.accepted, (
                f"'{example_name}': expected '{s}' to be accepted, got rejected."
            )

    @pytest.mark.parametrize("example_name", list(EXAMPLES.keys()))
    def test_example_rejects_listed_strings(self, example_name):
        nfa = get_example(example_name)
        example = EXAMPLES[example_name]
        for s in example["rejects"]:
            result = simulate_nfa(nfa, s)
            assert not result.accepted, (
                f"'{example_name}': expected '{s}' to be rejected, got accepted."
            )

    @pytest.mark.parametrize("example_name", list(EXAMPLES.keys()))
    def test_example_dfa_equivalence(self, example_name):
        nfa = get_example(example_name)
        example = EXAMPLES[example_name]
        all_strings = example["accepts"] + example["rejects"]
        mismatches = _check_equivalence(nfa, all_strings)
        assert mismatches == [], (
            f"'{example_name}': NFA/DFA mismatch on: {mismatches}"
        )
