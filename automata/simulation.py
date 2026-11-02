"""
Simulation of NFA and DFA on input strings.

NFA simulation uses a *set of active states* approach:
  - Begin with ε-closure of the initial state.
  - For each symbol, compute move() then ε-closure().
  - Accept if any active state is a final state.

DFA simulation is deterministic:
  - Begin at the initial state.
  - For each symbol, follow exactly one transition.
  - Accept if the final state is an accepting state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set

from .nfa import NFA, EPSILON
from .dfa import DFA
from .conversion import epsilon_closure, move


# ────────────────────────────────────────────────────────────────────────────
# Result data classes
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class NFASimStep:
    """One step of NFA simulation."""

    symbol: str | None          # None for the initial (before-input) step
    active_states: FrozenSet[str]


@dataclass
class NFASimResult:
    """Full result of simulating an NFA on an input string."""

    input_string: str
    steps: List[NFASimStep] = field(default_factory=list)
    accepted: bool = False
    rejection_reason: str = ""

    @property
    def final_states(self) -> FrozenSet[str]:
        if self.steps:
            return self.steps[-1].active_states
        return frozenset()


@dataclass
class DFASimStep:
    """One step of DFA simulation."""

    symbol: str | None          # None for the initial step
    current_state: FrozenSet[str]


@dataclass
class DFASimResult:
    """Full result of simulating a DFA on an input string."""

    input_string: str
    steps: List[DFASimStep] = field(default_factory=list)
    accepted: bool = False
    rejection_reason: str = ""

    @property
    def final_state(self) -> FrozenSet[str] | None:
        if self.steps:
            return self.steps[-1].current_state
        return None


# ────────────────────────────────────────────────────────────────────────────
# Simulation functions
# ────────────────────────────────────────────────────────────────────────────


def simulate_nfa(nfa: NFA, input_string: str) -> NFASimResult:
    """
    Simulate an NFA on *input_string*.

    Uses the standard set-of-states approach with ε-closure at each step.

    Parameters
    ----------
    nfa:
        The NFA to simulate.
    input_string:
        The string to test (may be empty).

    Returns
    -------
    NFASimResult
        Contains per-step active states and the accept/reject verdict.
    """
    result = NFASimResult(input_string=input_string)

    # Step 0: initial ε-closure
    active: FrozenSet[str] = epsilon_closure({nfa.initial_state}, nfa.transitions)
    result.steps.append(NFASimStep(symbol=None, active_states=active))

    for symbol in input_string:
        if symbol not in nfa.alphabet:
            result.accepted = False
            result.rejection_reason = (
                f"Symbol '{symbol}' is not in the alphabet {sorted(nfa.alphabet)}."
            )
            return result

        moved = move(active, symbol, nfa.transitions)
        active = epsilon_closure(moved, nfa.transitions)
        result.steps.append(NFASimStep(symbol=symbol, active_states=active))

    # Accept if at least one active state is a final state
    result.accepted = bool(active & nfa.final_states)
    if not result.accepted and active:
        result.rejection_reason = (
            f"None of the active states {set(active)} are accepting states "
            f"{nfa.final_states}."
        )
    elif not active:
        result.rejection_reason = "No active states remain (all paths died)."

    return result


def simulate_dfa(dfa: DFA, input_string: str) -> DFASimResult:
    """
    Simulate a DFA on *input_string*.

    Exactly one transition is followed per input symbol.

    Parameters
    ----------
    dfa:
        The DFA to simulate (produced by subset construction).
    input_string:
        The string to test.

    Returns
    -------
    DFASimResult
        Contains the state sequence and accept/reject verdict.
    """
    result = DFASimResult(input_string=input_string)

    current: FrozenSet[str] = dfa.initial_state
    result.steps.append(DFASimStep(symbol=None, current_state=current))

    for symbol in input_string:
        if symbol not in dfa.alphabet:
            result.accepted = False
            result.rejection_reason = (
                f"Symbol '{symbol}' is not in the alphabet {sorted(dfa.alphabet)}."
            )
            return result

        next_state = dfa.get_transition(current, symbol)
        if next_state is None:
            # Should not happen for a total DFA, but guard anyway
            result.accepted = False
            result.rejection_reason = (
                f"No transition defined for state "
                f"{dfa.format_state(current)!r} on symbol '{symbol}'."
            )
            return result

        current = next_state
        result.steps.append(DFASimStep(symbol=symbol, current_state=current))

    result.accepted = current in dfa.final_states
    if not result.accepted:
        result.rejection_reason = (
            f"Final state {dfa.format_state(current)!r} is not an accepting state."
        )

    return result
