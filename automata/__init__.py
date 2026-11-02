"""
Automata package for NFA to DFA conversion.

This package provides core data structures and algorithms for:
- Non-Deterministic Finite Automata (NFA)
- Deterministic Finite Automata (DFA)
- Subset Construction (NFA to DFA conversion)
- Simulation of input strings
- Validation of automata definitions
"""

from .nfa import NFA
from .dfa import DFA
from .conversion import nfa_to_dfa, epsilon_closure, move
from .simulation import simulate_nfa, simulate_dfa
from .validation import validate_automaton

__all__ = [
    "NFA",
    "DFA",
    "nfa_to_dfa",
    "epsilon_closure",
    "move",
    "simulate_nfa",
    "simulate_dfa",
    "validate_automaton",
]
