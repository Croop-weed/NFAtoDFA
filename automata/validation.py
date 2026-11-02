"""
Validation helpers for NFA and DFA instances.

Catches common user errors before conversion or simulation is attempted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .nfa import NFA, EPSILON
from .dfa import DFA


@dataclass
class ValidationResult:
    """Accumulates validation errors and warnings."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __bool__(self) -> bool:
        return self.is_valid


def validate_automaton(nfa: NFA) -> ValidationResult:
    """
    Validate an NFA definition and return a ValidationResult.

    Checks performed
    ----------------
    1. At least one state must exist.
    2. The alphabet must be non-empty.
    3. The initial state must be in Q.
    4. All final states must be in Q.
    5. All transition source states must be in Q.
    6. All transition destination states must be in Q.
    7. All transition symbols must be in Σ ∪ {ε}.
    8. Epsilon (ε) must NOT appear in the alphabet.
    9. Warning if some states are unreachable from q0.
    """
    v = ValidationResult()

    # ── 1. Non-empty state set ────────────────────────────────────────────
    if not nfa.states:
        v.errors.append("The automaton must have at least one state.")
        return v  # Abort early — further checks need states

    # ── 2. Non-empty alphabet ─────────────────────────────────────────────
    if not nfa.alphabet:
        v.errors.append("The input alphabet must be non-empty.")

    # ── 3. Initial state in Q ─────────────────────────────────────────────
    if not nfa.initial_state:
        v.errors.append("An initial state must be specified.")
    elif nfa.initial_state not in nfa.states:
        v.errors.append(
            f"Initial state '{nfa.initial_state}' is not in the state set Q = "
            f"{sorted(nfa.states)}."
        )

    # ── 4. Final states ⊆ Q ───────────────────────────────────────────────
    if not nfa.final_states:
        v.warnings.append("No accepting states defined — no string will be accepted.")
    for f in nfa.final_states:
        if f not in nfa.states:
            v.errors.append(
                f"Accepting state '{f}' is not in the state set Q = "
                f"{sorted(nfa.states)}."
            )

    # ── 8. ε must not appear in alphabet ─────────────────────────────────
    if EPSILON in nfa.alphabet:
        v.errors.append(
            "Epsilon (ε) must not appear in the input alphabet. "
            "ε-transitions are specified in the transition function only."
        )

    # ── 5 & 6 & 7. Validate transitions ──────────────────────────────────
    valid_symbols = nfa.alphabet | {EPSILON}
    for src, sym_map in nfa.transitions.items():
        if src not in nfa.states:
            v.errors.append(
                f"Transition source state '{src}' is not in Q = "
                f"{sorted(nfa.states)}."
            )
        for sym, dests in sym_map.items():
            if sym not in valid_symbols:
                v.errors.append(
                    f"Transition symbol '{sym}' from state '{src}' is not in "
                    f"Σ ∪ {{ε}} = {sorted(valid_symbols)}."
                )
            for dest in dests:
                if dest not in nfa.states:
                    v.errors.append(
                        f"Transition destination '{dest}' (from '{src}' on "
                        f"'{sym}') is not in Q = {sorted(nfa.states)}."
                    )

    # ── 9. Unreachable states (warning only) ──────────────────────────────
    if nfa.initial_state in nfa.states:
        reachable = nfa.reachable_states()
        unreachable = nfa.states - reachable
        if unreachable:
            v.warnings.append(
                f"States {sorted(unreachable)} are unreachable from the initial "
                f"state '{nfa.initial_state}'."
            )

    return v
