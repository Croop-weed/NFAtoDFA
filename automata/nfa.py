"""
Non-Deterministic Finite Automaton (NFA) data structure.

An NFA is formally defined as a 5-tuple:
    (Q, Σ, δ, q0, F)
where:
    Q  = finite set of states
    Σ  = finite input alphabet (does NOT include ε)
    δ  = transition function: Q × (Σ ∪ {ε}) → P(Q)
    q0 = initial state (q0 ∈ Q)
    F  = set of accepting states (F ⊆ Q)

Key difference from DFA: δ can return a *set* of states (possibly empty),
and ε-transitions (moves without consuming input) are allowed.
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Set

# Sentinel constant for epsilon (empty-string) transitions.
EPSILON = "ε"


@dataclass
class NFA:
    """
    Represents a Non-Deterministic Finite Automaton.

    Attributes
    ----------
    states : set[str]
        All states of the NFA (e.g., {"q0", "q1", "q2"}).
    alphabet : set[str]
        The input alphabet, *excluding* epsilon
        (e.g., {"0", "1"} or {"a", "b"}).
    transitions : dict[str, dict[str, set[str]]]
        Nested dict: state → symbol → {reachable states}.
        Use EPSILON as a key for ε-transitions.
        Example: {"q0": {"a": {"q1"}, EPSILON: {"q2"}}}
    initial_state : str
        The single start state.
    final_states : set[str]
        The set of accepting (final) states.
    """

    states: Set[str] = field(default_factory=set)
    alphabet: Set[str] = field(default_factory=set)
    # transitions[state][symbol] = {dest_state, ...}
    transitions: Dict[str, Dict[str, Set[str]]] = field(default_factory=dict)
    initial_state: str = ""
    final_states: Set[str] = field(default_factory=set)

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    def add_transition(self, from_state: str, symbol: str, to_states: Set[str]) -> None:
        """Add (or merge) a transition from *from_state* on *symbol*."""
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        if symbol not in self.transitions[from_state]:
            self.transitions[from_state][symbol] = set()
        self.transitions[from_state][symbol].update(to_states)

    def get_transitions(self, state: str, symbol: str) -> Set[str]:
        """Return the set of states reachable from *state* on *symbol*.

        Returns an empty set if no transition is defined.
        """
        return self.transitions.get(state, {}).get(symbol, set())

    def has_epsilon_transitions(self) -> bool:
        """Return True if any ε-transition exists in this NFA."""
        for sym_map in self.transitions.values():
            if EPSILON in sym_map:
                return True
        return False

    def reachable_states(self) -> Set[str]:
        """Return the set of states reachable from the initial state."""
        visited: Set[str] = set()
        stack = [self.initial_state]
        while stack:
            s = stack.pop()
            if s in visited:
                continue
            visited.add(s)
            for sym in list(self.transitions.get(s, {}).keys()):
                for t in self.transitions[s][sym]:
                    if t not in visited:
                        stack.append(t)
        return visited

    def to_dict(self) -> dict:
        """Serialise the NFA to a plain dict (useful for JSON export)."""
        return {
            "states": sorted(self.states),
            "alphabet": sorted(self.alphabet),
            "initial_state": self.initial_state,
            "final_states": sorted(self.final_states),
            "transitions": {
                state: {sym: sorted(dests) for sym, dests in sym_map.items()}
                for state, sym_map in self.transitions.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NFA":
        """Deserialise an NFA from a plain dict."""
        nfa = cls(
            states=set(data["states"]),
            alphabet=set(data["alphabet"]),
            initial_state=data["initial_state"],
            final_states=set(data["final_states"]),
        )
        for state, sym_map in data.get("transitions", {}).items():
            for sym, dests in sym_map.items():
                nfa.add_transition(state, sym, set(dests))
        return nfa

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"NFA(states={self.states}, alphabet={self.alphabet}, "
            f"initial={self.initial_state!r}, finals={self.final_states})"
        )
