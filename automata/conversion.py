"""
Subset Construction Algorithm — NFA → DFA conversion.

This module implements the classical subset construction (also called
the *powerset construction*) algorithm.  The algorithm is completely
independent of any UI framework so it can be tested in isolation.

Algorithm outline
-----------------
1. Compute ε-closure(q0_nfa) → this becomes the DFA start state.
2. Maintain a worklist of DFA states that still need transitions.
3. For each DFA state S and each alphabet symbol a:
       T = ε-closure( move(S, a) )
   Add T to the DFA (if not already seen) and record δ'(S, a) = T.
4. A DFA state S is accepting iff S ∩ F_nfa ≠ ∅.
5. Repeat until the worklist is empty.

The dead/trap state (∅) is added only when needed (lazy generation),
keeping the DFA minimal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set, Tuple

from .nfa import NFA, EPSILON
from .dfa import DFA


# ────────────────────────────────────────────────────────────────────────────
# Public primitive functions (tested independently)
# ────────────────────────────────────────────────────────────────────────────


def epsilon_closure(
    states: Set[str] | FrozenSet[str],
    transitions: Dict[str, Dict[str, Set[str]]],
) -> FrozenSet[str]:
    """
    Compute the ε-closure of a set of NFA states.

    The ε-closure of a set S is the set of all NFA states reachable
    from any state in S by following *zero or more* ε-transitions.

    Parameters
    ----------
    states:
        The seed set of NFA states.
    transitions:
        The NFA transition function
        (``nfa.transitions`` dict of dicts).

    Returns
    -------
    frozenset[str]
        The ε-closure of *states*.
    """
    closure: Set[str] = set(states)
    stack: List[str] = list(states)

    while stack:
        s = stack.pop()
        # Follow all ε-transitions from s
        for t in transitions.get(s, {}).get(EPSILON, set()):
            if t not in closure:
                closure.add(t)
                stack.append(t)

    return frozenset(closure)


def move(
    states: Set[str] | FrozenSet[str],
    symbol: str,
    transitions: Dict[str, Dict[str, Set[str]]],
) -> FrozenSet[str]:
    """
    Compute move(S, a) — the set of NFA states reachable from any
    state in S by consuming exactly one symbol *a* (no ε-transitions).

    Parameters
    ----------
    states:
        The current set of NFA states.
    symbol:
        The input symbol to consume.
    transitions:
        The NFA transition function.

    Returns
    -------
    frozenset[str]
        The set of NFA states reached after the move.
    """
    result: Set[str] = set()
    for s in states:
        result.update(transitions.get(s, {}).get(symbol, set()))
    return frozenset(result)


# ────────────────────────────────────────────────────────────────────────────
# Step record — used for the educational step-by-step explanation
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class ConversionStep:
    """Captures all intermediate values for one DFA transition computation."""

    dfa_state: FrozenSet[str]          # Current DFA state (NFA subset)
    symbol: str                         # Input symbol being processed
    move_result: FrozenSet[str]         # move(dfa_state, symbol)
    closure_result: FrozenSet[str]      # ε-closure(move_result)
    is_new_state: bool                  # Was closure_result newly discovered?

    def format_set(self, s: FrozenSet[str]) -> str:
        if not s:
            return "∅"
        return "{" + ", ".join(sorted(s)) + "}"

    @property
    def dfa_state_str(self) -> str:
        return self.format_set(self.dfa_state)

    @property
    def move_result_str(self) -> str:
        return self.format_set(self.move_result)

    @property
    def closure_result_str(self) -> str:
        return self.format_set(self.closure_result)

    def explain(self) -> str:
        """Return a human-readable explanation of this step."""
        lines = [
            f"**DFA State:** {self.dfa_state_str}",
            f"**Input Symbol:** {self.symbol}",
            f"**move({self.dfa_state_str}, {self.symbol})** = {self.move_result_str}",
            f"**ε-closure({self.move_result_str})** = {self.closure_result_str}",
            f"**→ δ'({self.dfa_state_str}, {self.symbol}) = {self.closure_result_str}**",
        ]
        if self.is_new_state:
            lines.append(f"  *(New DFA state discovered: {self.closure_result_str})*")
        return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# Main conversion function
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class ConversionResult:
    """
    Full output of the NFA → DFA conversion.

    Attributes
    ----------
    dfa:
        The constructed DFA.
    steps:
        Ordered list of ConversionStep objects for the step-by-step UI.
    epsilon_closures:
        Mapping from every NFA state → its individual ε-closure.
        Useful for display in the 'ε-closure table'.
    """

    dfa: DFA
    steps: List[ConversionStep] = field(default_factory=list)
    epsilon_closures: Dict[str, FrozenSet[str]] = field(default_factory=dict)


def nfa_to_dfa(nfa: NFA) -> ConversionResult:
    """
    Convert an NFA to an equivalent DFA using subset construction.

    Parameters
    ----------
    nfa:
        A fully-specified NFA instance.

    Returns
    -------
    ConversionResult
        Contains the DFA, conversion steps, and ε-closure table.
    """
    # ── Pre-compute ε-closure for every individual NFA state ──────────────
    individual_closures: Dict[str, FrozenSet[str]] = {
        s: epsilon_closure({s}, nfa.transitions) for s in nfa.states
    }

    # ── Initialise the DFA ─────────────────────────────────────────────────
    dfa = DFA(alphabet=set(nfa.alphabet))

    # The DFA start state is the ε-closure of the NFA start state
    start: FrozenSet[str] = epsilon_closure({nfa.initial_state}, nfa.transitions)
    dfa.initial_state = start
    dfa.states.add(start)

    if start & nfa.final_states:
        dfa.final_states.add(start)

    # Worklist of DFA states whose outgoing transitions haven't been computed
    worklist: List[FrozenSet[str]] = [start]
    visited: Set[FrozenSet[str]] = {start}

    steps: List[ConversionStep] = []

    # ── Main subset-construction loop ──────────────────────────────────────
    while worklist:
        current: FrozenSet[str] = worklist.pop(0)  # BFS order for clarity

        for symbol in sorted(nfa.alphabet):          # deterministic ordering
            moved = move(current, symbol, nfa.transitions)
            closed = epsilon_closure(moved, nfa.transitions)

            is_new = closed not in visited

            if closed:  # Only record non-empty states (lazy dead-state)
                if is_new:
                    dfa.states.add(closed)
                    visited.add(closed)
                    worklist.append(closed)
                    if closed & nfa.final_states:
                        dfa.final_states.add(closed)

                dfa.add_transition(current, symbol, closed)
            else:
                # The dead state (∅) is reached — add it lazily
                dead: FrozenSet[str] = frozenset()
                if dead not in visited:
                    dfa.states.add(dead)
                    visited.add(dead)
                    worklist.append(dead)
                    # Dead state is never accepting
                dfa.add_transition(current, symbol, dead)

            steps.append(
                ConversionStep(
                    dfa_state=current,
                    symbol=symbol,
                    move_result=moved,
                    closure_result=closed,
                    is_new_state=is_new,
                )
            )

    return ConversionResult(
        dfa=dfa,
        steps=steps,
        epsilon_closures=individual_closures,
    )
