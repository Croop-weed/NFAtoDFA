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

import html
import json
from typing import Dict, FrozenSet, Tuple

import graphviz
from pyvis.network import Network

from automata.nfa import NFA, EPSILON
from automata.dfa import DFA


# ────────────────────────────────────────────────────────────────────────────
# Color palette (dark-mode friendly)
# ────────────────────────────────────────────────────────────────────────────
_STYLE = {
    "bgcolor": "#1e1e1e",
    "node_default": {
        "style": "filled",
        "fillcolor": "#30363a",
        "color": "#89969e",
        "fontcolor": "#f1f3f4",
        "fontname": "Helvetica Neue",
        "fontsize": "13",
        "penwidth": "1.8",
    },
    "node_final": {
        "style": "filled",
        "fillcolor": "#294438",
        "color": "#87bd98",
        "fontcolor": "#f1f3f4",
        "fontname": "Helvetica Neue",
        "fontsize": "13",
        "penwidth": "2.5",
    },
    "edge": {
        "color": "#91a0a8",
        "fontcolor": "#d8dee2",
        "fontname": "Helvetica Neue",
        "fontsize": "12",
        "penwidth": "1.5",
        "arrowsize": "0.8",
    },
    "start_edge": {
        "color": "#e34b4b",
        "penwidth": "2.0",
        "arrowsize": "1.0",
    },
}

_INTERACTIVE_COLORS = {
    "background": "#30363a",
    "border": "#8a969d",
    "highlight": {"background": "#3a4247", "border": "#e34b4b"},
    "hover": {"background": "#3a4247", "border": "#e34b4b"},
    "final_background": "#294438",
    "final_border": "#87bd98",
    "edge": "#a7b0b5",
    "start": "#e34b4b",
    "epsilon": "#e0b15a",
    "text": "#f1f3f4",
    "muted": "#aeb7bc",
    "background_canvas": "#202326",
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


def _interactive_network(
    *,
    layout: str,
    physics: bool,
    show_edge_labels: bool,
    node_spacing: int,
) -> Network:
    """Create a locally self-contained, interactive network canvas."""
    network = Network(
        height="620px",
        width="100%",
        directed=True,
        bgcolor=_INTERACTIVE_COLORS["background_canvas"],
        font_color=_INTERACTIVE_COLORS["text"],
        cdn_resources="in_line",
    )
    network.toggle_physics(physics and layout == "Physics")
    network.set_options(
        json.dumps(
            {
                "interaction": {
                    "hover": True,
                    "navigationButtons": True,
                    "keyboard": {"enabled": True, "bindToWindow": False},
                    "multiselect": True,
                },
                "nodes": {
                    "font": {"face": "IBM Plex Sans, sans-serif", "size": 18},
                    "borderWidth": 2,
                    "borderWidthSelected": 4,
                    "shadow": {"enabled": True, "color": "rgba(0,0,0,0.28)", "size": 12, "x": 0, "y": 4},
                },
                "edges": {
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.75}},
                    "color": {"color": _INTERACTIVE_COLORS["edge"], "highlight": _INTERACTIVE_COLORS["start"]},
                    "font": {"color": _INTERACTIVE_COLORS["text"], "face": "IBM Plex Mono, monospace", "size": 14, "strokeWidth": 4, "strokeColor": _INTERACTIVE_COLORS["background_canvas"]},
                    "smooth": {"enabled": True, "type": "dynamic", "roundness": 0.35},
                    "width": 1.7,
                },
                "layout": {
                    "improvedLayout": True,
                    "hierarchical": {
                        "enabled": layout == "Hierarchical",
                        "direction": "LR",
                        "sortMethod": "directed",
                        "levelSeparation": node_spacing,
                        "nodeSpacing": max(100, node_spacing - 30),
                        "treeSpacing": node_spacing,
                        "blockShifting": True,
                        "edgeMinimization": True,
                        "parentCentralization": True,
                    },
                },
                "physics": {
                    "enabled": physics and layout == "Physics",
                    "solver": "forceAtlas2Based",
                    "forceAtlas2Based": {
                        "gravitationalConstant": -45,
                        "centralGravity": 0.012,
                        "springLength": node_spacing,
                        "springConstant": 0.08,
                        "damping": 0.42,
                        "avoidOverlap": 0.8,
                    },
                    "stabilization": {"enabled": True, "iterations": 180, "fit": True},
                },
            }
        )
    )
    return network


def _add_interactive_state(
    network: Network,
    state_id: str,
    label: str,
    *,
    is_initial: bool,
    is_final: bool,
    tooltip: str,
) -> None:
    background = _INTERACTIVE_COLORS["final_background"] if is_final else _INTERACTIVE_COLORS["background"]
    border = _INTERACTIVE_COLORS["start"] if is_initial else (
        _INTERACTIVE_COLORS["final_border"] if is_final else _INTERACTIVE_COLORS["border"]
    )
    network.add_node(
        state_id,
        label=label,
        title=html.escape(tooltip),
        shape="dot",
        size=25 if is_initial else 22,
        color={
            "background": background,
            "border": border,
            "highlight": {"background": "#3a4247", "border": _INTERACTIVE_COLORS["start"]},
            "hover": {"background": "#3a4247", "border": _INTERACTIVE_COLORS["start"]},
        },
        borderWidth=4 if is_initial else 3 if is_final else 2,
        font={"color": _INTERACTIVE_COLORS["text"], "face": "IBM Plex Sans, sans-serif", "size": 18},
    )


def render_nfa_interactive(
    nfa: NFA,
    *,
    layout: str = "Physics",
    physics: bool = True,
    show_edge_labels: bool = True,
    node_spacing: int = 180,
) -> str:
    """Build an interactive NFA diagram with draggable states and zoom controls."""
    network = _interactive_network(
        layout=layout,
        physics=physics,
        show_edge_labels=show_edge_labels,
        node_spacing=node_spacing,
    )
    start_id = "__autometa_start__"
    while start_id in nfa.states:
        start_id = f"_{start_id}"

    network.add_node(
        start_id,
        label="START",
        title="Initial state marker",
        shape="box",
        size=12,
        color={"background": _INTERACTIVE_COLORS["start"], "border": _INTERACTIVE_COLORS["start"]},
        font={"color": _INTERACTIVE_COLORS["muted"], "face": "IBM Plex Sans, sans-serif", "size": 13},
    )
    for state in sorted(nfa.states):
        is_final = state in nfa.final_states
        role = "Initial, accepting" if state == nfa.initial_state and is_final else (
            "Initial" if state == nfa.initial_state else "Accepting" if is_final else "Regular"
        )
        _add_interactive_state(
            network,
            state,
            state,
            is_initial=state == nfa.initial_state,
            is_final=is_final,
            tooltip=f"{state} · {role} state",
        )
    network.add_edge(
        start_id,
        nfa.initial_state,
        color=_INTERACTIVE_COLORS["start"],
        width=2.5,
        arrows="to",
        smooth={"enabled": True, "type": "curvedCW", "roundness": 0.15},
    )

    labels: Dict[Tuple[str, str], list[str]] = {}
    for source, symbol_map in nfa.transitions.items():
        for symbol, destinations in symbol_map.items():
            for destination in destinations:
                labels.setdefault((source, destination), []).append(symbol)
    for (source, destination), symbols in sorted(labels.items()):
        merged_label = ", ".join(sorted(symbols))
        is_epsilon = EPSILON in symbols
        network.add_edge(
            source,
            destination,
            label=merged_label if show_edge_labels else "",
            title=f"{html.escape(source)} → {html.escape(destination)}: {html.escape(merged_label)}",
            color=_INTERACTIVE_COLORS["epsilon"] if is_epsilon else _INTERACTIVE_COLORS["edge"],
            font={"color": _INTERACTIVE_COLORS["epsilon"] if is_epsilon else _INTERACTIVE_COLORS["text"]},
        )
    return network.generate_html()


def render_dfa_interactive(
    dfa: DFA,
    *,
    layout: str = "Physics",
    physics: bool = True,
    show_edge_labels: bool = True,
    node_spacing: int = 180,
) -> str:
    """Build an interactive DFA diagram with draggable states and zoom controls."""
    network = _interactive_network(
        layout=layout,
        physics=physics,
        show_edge_labels=show_edge_labels,
        node_spacing=node_spacing,
    )
    states = sorted(dfa.states, key=lambda state: sorted(state))
    state_ids = {state: f"dfa_state_{index}" for index, state in enumerate(states)}
    start_id = "__autometa_dfa_start__"
    network.add_node(
        start_id,
        label="START",
        title="Initial state marker",
        shape="box",
        size=12,
        color={"background": _INTERACTIVE_COLORS["start"], "border": _INTERACTIVE_COLORS["start"]},
        font={"color": _INTERACTIVE_COLORS["muted"], "face": "IBM Plex Sans, sans-serif", "size": 13},
    )
    for state in states:
        label = "∅" if not state else "{" + ", ".join(sorted(state)) + "}"
        is_final = state in dfa.final_states
        role = "Initial, accepting" if state == dfa.initial_state and is_final else (
            "Initial" if state == dfa.initial_state else "Accepting" if is_final else "Regular"
        )
        if not state:
            role = "Dead state"
        _add_interactive_state(
            network,
            state_ids[state],
            label,
            is_initial=state == dfa.initial_state,
            is_final=is_final,
            tooltip=f"{label} · {role} DFA state",
        )
    network.add_edge(
        start_id,
        state_ids[dfa.initial_state],
        color=_INTERACTIVE_COLORS["start"],
        width=2.5,
        arrows="to",
    )
    for source, symbol_map in dfa.transitions.items():
        for symbol, destination in symbol_map.items():
            network.add_edge(
                state_ids[source],
                state_ids[destination],
                label=symbol if show_edge_labels else "",
                title=f"{html.escape(symbol)} transition",
                color=_INTERACTIVE_COLORS["edge"],
                font={"color": _INTERACTIVE_COLORS["text"]},
            )
    return network.generate_html()


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
