"""
Preloaded NFA examples for the simulator.

Each example is a dict that can be loaded into an NFA via NFA.from_dict().
"""

from __future__ import annotations

from automata.nfa import NFA, EPSILON

# ────────────────────────────────────────────────────────────────────────────
# Example 1 — Strings ending in 'ba'  (alphabet: {a, b})
# ────────────────────────────────────────────────────────────────────────────
_ENDING_BA = {
    "name": "Strings ending in 'ba'",
    "description": (
        "Accepts all strings over {a, b} that **end with 'ba'**.\n\n"
        "States: q0 (start), q1 (seen 'b'), q2 (seen 'ba' — accepting)\n\n"
        "Logic:\n"
        "- From q0, any 'a' or 'b' loops on q0 (keep scanning).\n"
        "- Seeing 'b' from q0 also non-deterministically moves to q1 "
        "(guessing we're at the start of the final 'ba').\n"
        "- From q1, seeing 'a' moves to q2 (accepting).\n"
        "- q2 has no outgoing transitions (the string must end here)."
    ),
    "accepts": ["ba", "aba", "bba", "abba", "baba"],
    "rejects": ["", "a", "b", "ab", "bb", "bab"],
    "data": {
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "initial_state": "q0",
        "final_states": ["q2"],
        "transitions": {
            "q0": {
                "a": ["q0"],
                "b": ["q0", "q1"],
            },
            "q1": {
                "a": ["q2"],
            },
        },
    },
}

# ────────────────────────────────────────────────────────────────────────────
# Example 2 — Strings containing 'abb'  (alphabet: {a, b})
# ────────────────────────────────────────────────────────────────────────────
_CONTAINING_ABB = {
    "name": "Strings containing 'abb'",
    "description": (
        "Accepts all strings over {a, b} that **contain the substring 'abb'**.\n\n"
        "States: q0 (start), q1 (seen 'a'), q2 (seen 'ab'), "
        "q3 (seen 'abb' — accepting)\n\n"
        "Logic:\n"
        "- q0 loops on 'a' and 'b' until 'a' starts the pattern.\n"
        "- q0 →[a]→ q1 (tentatively started 'abb').\n"
        "- q1 →[b]→ q2, q2 →[b]→ q3 (pattern complete).\n"
        "- q3 loops on both symbols (anything after 'abb' is fine)."
    ),
    "accepts": ["abb", "aabb", "abbb", "babb", "bbabb"],
    "rejects": ["", "a", "b", "ab", "ba", "bba"],
    "data": {
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "initial_state": "q0",
        "final_states": ["q3"],
        "transitions": {
            "q0": {
                "a": ["q0", "q1"],
                "b": ["q0"],
            },
            "q1": {
                "b": ["q2"],
            },
            "q2": {
                "b": ["q3"],
            },
            "q3": {
                "a": ["q3"],
                "b": ["q3"],
            },
        },
    },
}

# ────────────────────────────────────────────────────────────────────────────
# Example 3 — ε-transitions: strings over {0,1} where 2nd symbol from end is 1
# ────────────────────────────────────────────────────────────────────────────
_EPSILON_EXAMPLE = {
    "name": "ε-transitions: second-to-last symbol is 1",
    "description": (
        "Accepts strings over {0, 1} where the **second-to-last symbol is '1'**.\n\n"
        "States: q0 (start), q1 (guessing we're at 2nd-to-last '1'), "
        "q2 (accepting after one more symbol)\n\n"
        "Demonstrates ε-transitions:\n"
        "- q0 loops on both 0 and 1 (non-deterministically choose to stay).\n"
        "- q0 →[1]→ q1 (guess this '1' is the second-to-last symbol).\n"
        "- q1 →[0]→ q2, q1 →[1]→ q2 (consume the last symbol).\n"
        "- Additionally, q0 has an ε-transition to a helper state qh that "
        "models an alternative path — used here to show ε-closure in action."
    ),
    "accepts": ["10", "11", "010", "110", "011", "111", "0110"],
    "rejects": ["", "0", "1", "00", "01", "000", "001"],
    "data": {
        "states": ["q0", "qh", "q1", "q2"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "final_states": ["q2"],
        "transitions": {
            "q0": {
                "0": ["q0"],
                "1": ["q0", "q1"],
                EPSILON: ["qh"],
            },
            "qh": {
                "0": ["qh"],
                "1": ["qh"],
            },
            "q1": {
                "0": ["q2"],
                "1": ["q2"],
            },
        },
    },
}

# ────────────────────────────────────────────────────────────────────────────
# Example 4 — Classic textbook: strings over {0,1} ending in '01'
# ────────────────────────────────────────────────────────────────────────────
_ENDING_01 = {
    "name": "Strings ending in '01'",
    "description": (
        "Accepts all binary strings that **end with '01'**.\n\n"
        "States: A (start), B (seen '0'), C (seen '01' — accepting)\n\n"
        "Mirrors the classic textbook example:\n"
        "- A loops on '0' and '1' (keep scanning).\n"
        "- A →[0]→ B (guessing last two are '0?').\n"
        "- B →[1]→ C (pattern '01' complete).\n"
        "- C has no outgoing transitions."
    ),
    "accepts": ["01", "001", "101", "0101", "1001"],
    "rejects": ["", "0", "1", "10", "00", "11", "010"],
    "data": {
        "states": ["A", "B", "C"],
        "alphabet": ["0", "1"],
        "initial_state": "A",
        "final_states": ["C"],
        "transitions": {
            "A": {
                "0": ["A", "B"],
                "1": ["A"],
            },
            "B": {
                "1": ["C"],
            },
        },
    },
}

# ────────────────────────────────────────────────────────────────────────────
# Registry
# ────────────────────────────────────────────────────────────────────────────

EXAMPLES: dict[str, dict] = {
    "Strings ending in 'ba'": _ENDING_BA,
    "Strings containing 'abb'": _CONTAINING_ABB,
    "ε-transitions: second-to-last is 1": _EPSILON_EXAMPLE,
    "Strings ending in '01'": _ENDING_01,
}


def get_example(name: str) -> NFA:
    """Return an NFA for the named example.

    Parameters
    ----------
    name:
        One of the keys of EXAMPLES.

    Returns
    -------
    NFA
        A fully-constructed NFA instance.

    Raises
    ------
    KeyError
        If *name* is not a recognised example.
    """
    entry = EXAMPLES[name]
    return NFA.from_dict(entry["data"])
