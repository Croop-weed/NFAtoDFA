"""
Graph rendering for NFA and DFA using Graphviz.

Conventions
-----------
- Initial state: preceded by an invisible entry node with an arrow.
- Accepting states: rendered with a double circle (shape=doublecircle).
- Multiple transitions between the same two states are merged into a
  single edge with labels joined by commas.
- ε-transitions are labelled with the ε character.
- DFA states show the NFA subset they correspond to.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

import graphviz

from automata.nfa import NFA, EPSILON
from automata.dfa import DFA


# ────────────────────────────────────────────────────────────────────────────
# Color palette (dark-mode friendly)
# ────────────────────────────────────────────────────────────────────────────
_STYLE = {
    "bgcolor": "#0f172a",
    "node_default": {
        "style": "filled",
        "fillcolor": "#1e293b",
        "color": "#38bdf8",
        "fontcolor": "#e2e8f0",
        "fontname": "Helvetica Neue",
        "fontsize": "13",
        "penwidth": "1.8",
    },
    "node_final": {
        "style": "filled",
        "fillcolor": "#164e63",
        "color": "#22d3ee",
        "fontcolor": "#e2e8f0",
        "fontname": "Helvetica Neue",
        "fontsize": "13",
        "penwidth": "2.5",
    },
    "edge": {
        "color": "#94a3b8",
        "fontcolor": "#cbd5e1",
        "fontname": "Helvetica Neue",
        "fontsize": "12",
        "penwidth": "1.5",
        "arrowsize": "0.8",
    },
    "start_edge": {
        "color": "#4ade80",
        "penwidth": "2.0",
        "arrowsize": "1.0",
    },
}


def _apply_attrs(obj, attrs: dict) -> None:
    """Set multiple attributes on a graphviz node/edge."""
    for k, v in attrs.items():
        obj.attr(**{k: v})


def _merge_labels(
    edges: Dict[Tuple[str, str], list[str]]
) -> Dict[Tuple[str, str], str]:
    """Merge multiple edge labels between the same pair of nodes."""
    return {pair: ", ".join(sorted(labels)) for pair, labels in edges.items()}


# ────────────────────────────────────────────────────────────────────────────
# NFA renderer
# ────────────────────────────────────────────────────────────────────────────


def render_nfa(nfa: NFA, name: str = "NFA") -> graphviz.Digraph:
    """
    Render an NFA as a Graphviz Digraph.

    Parameters
    ----------
    nfa:
        The NFA to visualise.
    name:
        Graph title used as the Graphviz name.

    Returns
    -------
    graphviz.Digraph
        Ready-to-render graph object.
    """
    dot = graphviz.Digraph(name=name, graph_attr={"rankdir": "LR", "bgcolor": _STYLE["bgcolor"]})

    # ── Nodes ───────────────────────────────────────────────────────────
    for state in sorted(nfa.states):
        is_final = state in nfa.final_states
        attrs = dict(_STYLE["node_final"] if is_final else _STYLE["node_default"])
        shape = "doublecircle" if is_final else "circle"
        dot.node(state, label=state, shape=shape, **attrs)

    # Invisible start node
    dot.node("__start__", label="", shape="point", width="0.01",
             style="invis", color="#0f172a")
    dot.edge("__start__", nfa.initial_state, **_STYLE["start_edge"])

    # ── Edges (merge parallel edges) ────────────────────────────────────
    edge_labels: Dict[Tuple[str, str], list[str]] = {}
    for src, sym_map in nfa.transitions.items():
        for sym, dests in sym_map.items():
            label = sym  # EPSILON is already "ε"
            for dest in sorted(dests):
                key = (src, dest)
                edge_labels.setdefault(key, []).append(label)

    for (src, dest), labels in _merge_labels(edge_labels).items():
        dot.edge(src, dest, label=labels, **_STYLE["edge"])

    return dot


# ────────────────────────────────────────────────────────────────────────────
# DFA renderer
# ────────────────────────────────────────────────────────────────────────────


def render_dfa(dfa: DFA, name: str = "DFA") -> graphviz.Digraph:
    """
    Render a DFA (produced by subset construction) as a Graphviz Digraph.

    Each DFA state is labelled with its NFA subset for educational clarity.

    Parameters
    ----------
    dfa:
        The DFA to visualise.
    name:
        Graph title.

    Returns
    -------
    graphviz.Digraph
        Ready-to-render graph object.
    """
    dot = graphviz.Digraph(name=name, graph_attr={"rankdir": "LR", "bgcolor": _STYLE["bgcolor"]})

    def _node_id(state: FrozenSet[str]) -> str:
        """Stable, unique node identifier for a DFA state."""
        if not state:
            return "__dead__"
        return "_".join(sorted(state))

    def _node_label(state: FrozenSet[str]) -> str:
        if not state:
            return "∅"
        return "{" + ", ".join(sorted(state)) + "}"

    # ── Nodes ───────────────────────────────────────────────────────────
    for state in sorted(dfa.states, key=lambda s: sorted(s)):
        is_final = state in dfa.final_states
        is_dead = len(state) == 0
        attrs = dict(_STYLE["node_final"] if is_final else _STYLE["node_default"])
        if is_dead:
            attrs["fillcolor"] = "#2d1515"
            attrs["color"] = "#ef4444"
        shape = "doublecircle" if is_final else "circle"
        dot.node(_node_id(state), label=_node_label(state), shape=shape, **attrs)

    # Invisible start node
    dot.node("__dfa_start__", label="", shape="point", width="0.01",
             style="invis", color="#0f172a")
    dot.edge("__dfa_start__", _node_id(dfa.initial_state), **_STYLE["start_edge"])

    # ── Edges (merge parallel edges) ────────────────────────────────────
    edge_labels: Dict[Tuple[str, str], list[str]] = {}
    for src_state, sym_map in dfa.transitions.items():
        for sym, dest_state in sym_map.items():
            key = (_node_id(src_state), _node_id(dest_state))
            edge_labels.setdefault(key, []).append(sym)

    for (src_id, dest_id), labels in _merge_labels(edge_labels).items():
        dot.edge(src_id, dest_id, label=", ".join(sorted(labels)), **_STYLE["edge"])

    return dot
