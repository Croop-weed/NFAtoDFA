"""
Deterministic Finite Automaton (DFA) data structure.

A DFA is formally defined as a 5-tuple:
    (Q', Σ, δ', q0', F')
where each state in Q' corresponds to a *subset* of NFA states,
produced by the Subset Construction algorithm.

Key property: δ' is a *total* function — every (state, symbol) pair
maps to exactly one state (possibly the dead/trap state ∅).
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional, Set


# The dead (trap) state is represented as the empty frozenset.
DEAD_STATE: FrozenSet[str] = frozenset()


@dataclass
class DFA:
    """
    Represents a Deterministic Finite Automaton produced by subset construction.

    Each DFA state is a *frozenset* of NFA state names — this makes
    equality checks and hashing straightforward.

    Attributes
    ----------
    states : set[frozenset[str]]
        All DFA states, each being a frozen subset of NFA states.
    alphabet : set[str]
        Input alphabet (inherited from the original NFA).
    transitions : dict[frozenset[str], dict[str, frozenset[str]]]
        Deterministic transition function: state × symbol → state.
    initial_state : frozenset[str]
        The start state (ε-closure of the NFA initial state).
    final_states : set[frozenset[str]]
        Accepting states — any DFA state that contains at least one
        NFA accepting state.
    state_labels : dict[frozenset[str], str]
        Optional human-readable labels (e.g., "q0", "q1") for display.
    """

    states: Set[FrozenSet[str]] = field(default_factory=set)
    alphabet: Set[str] = field(default_factory=set)
    transitions: Dict[FrozenSet[str], Dict[str, FrozenSet[str]]] = field(
        default_factory=dict
    )
    initial_state: FrozenSet[str] = field(default_factory=frozenset)
    final_states: Set[FrozenSet[str]] = field(default_factory=set)
    # Optional mapping from frozenset → short label for display
    state_labels: Dict[FrozenSet[str], str] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    def add_transition(
        self,
        from_state: FrozenSet[str],
        symbol: str,
        to_state: FrozenSet[str],
    ) -> None:
        """Record a deterministic transition."""
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        self.transitions[from_state][symbol] = to_state

    def get_transition(
        self, state: FrozenSet[str], symbol: str
    ) -> Optional[FrozenSet[str]]:
        """Return the unique next state, or None if undefined."""
        return self.transitions.get(state, {}).get(symbol)

    def format_state(self, state: FrozenSet[str]) -> str:
        """Return a display-friendly string for a DFA state.

        Uses custom label if available, otherwise formats the subset.
        """
        if state in self.state_labels:
            return self.state_labels[state]
        if not state:
            return "∅"
        return "{" + ", ".join(sorted(state)) + "}"

    def assign_short_labels(self) -> None:
        """
        Assign sequential short labels (D0, D1, …) to all DFA states,
        with D0 always being the initial state.
        """
        ordered = [self.initial_state] + sorted(
            (s for s in self.states if s != self.initial_state),
            key=lambda s: sorted(s),
        )
        for i, state in enumerate(ordered):
            self.state_labels[state] = f"D{i}"

    def get_transition_table(self) -> list[dict]:
        """
        Return the transition table as a list of row-dicts, suitable for
        display in a DataFrame or CSV export.
        """
        rows = []
        for state in sorted(self.states, key=lambda s: sorted(s)):
            row: dict = {
                "DFA State": self.format_state(state),
                "NFA Subset": "{" + ", ".join(sorted(state)) + "}" if state else "∅",
                "Is Accepting": state in self.final_states,
                "Is Initial": state == self.initial_state,
            }
            for sym in sorted(self.alphabet):
                dest = self.get_transition(state, sym)
                row[sym] = self.format_state(dest) if dest is not None else "—"
            rows.append(row)
        return rows

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DFA(|states|={len(self.states)}, alphabet={self.alphabet}, "
            f"initial={self.format_state(self.initial_state)}, "
            f"|finals|={len(self.final_states)})"
        )
