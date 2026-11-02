"""
NFA to DFA Simulator — Streamlit Application
============================================

A complete interactive educational tool for understanding the
Subset Construction Algorithm (NFA → DFA conversion).

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import streamlit as st

from automata.nfa import NFA, EPSILON
from automata.conversion import nfa_to_dfa, ConversionResult
from automata.simulation import simulate_nfa, simulate_dfa
from automata.validation import validate_automaton
from examples.sample_nfas import EXAMPLES, get_example
from visualization.graph import render_nfa, render_dfa

# ────────────────────────────────────────────────────────────────────────────
# Page config & Global CSS
# ────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NFA → DFA Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary:   #0f172a;
    --bg-card:      #1e293b;
    --bg-card2:     #162032;
    --accent-blue:  #38bdf8;
    --accent-cyan:  #22d3ee;
    --accent-green: #4ade80;
    --accent-amber: #fbbf24;
    --accent-rose:  #fb7185;
    --accent-violet:#a78bfa;
    --text-primary: #e2e8f0;
    --text-muted:   #94a3b8;
    --border:       #334155;
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1a2744 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .stRadio > label {
    color: var(--text-muted) !important;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Section header cards ── */
.section-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 60%);
    border: 1px solid var(--accent-blue);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 28px;
}
.section-header h1 { margin: 0 0 6px 0; font-size: 1.9rem; color: var(--accent-blue); }
.section-header p  { margin: 0; color: var(--text-muted); font-size: 0.95rem; }

/* ── Info card ── */
.info-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
}

/* ── Step card ── */
.step-card {
    background: linear-gradient(135deg, #1a2744, #1e293b);
    border-left: 4px solid var(--accent-cyan);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 14px;
    font-size: 0.92rem;
}

/* ── Accept / Reject badges ── */
.badge-accept {
    display: inline-block;
    background: #14532d;
    color: var(--accent-green);
    border: 1px solid var(--accent-green);
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 600;
    font-size: 0.88rem;
}
.badge-reject {
    display: inline-block;
    background: #450a0a;
    color: var(--accent-rose);
    border: 1px solid var(--accent-rose);
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 600;
    font-size: 0.88rem;
}

/* ── Metric tiles ── */
.metric-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }
.metric-tile {
    flex: 1; min-width: 120px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.metric-tile .val { font-size: 2rem; font-weight: 700; color: var(--accent-blue); }
.metric-tile .lbl { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }

/* ── Monospace spans ── */
.mono { font-family: 'JetBrains Mono', monospace; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    border-radius: 8px;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #1e3a5f !important;
    color: var(--accent-blue) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0369a1, #0e7490) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0284c7, #06b6d4) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(56,189,248,0.3) !important;
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--bg-card2) !important;
    border-radius: 8px !important;
    color: var(--accent-blue) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────────────────
# Session state helpers
# ────────────────────────────────────────────────────────────────────────────

def _init_session() -> None:
    defaults: dict[str, Any] = {
        "nfa": None,
        "conversion_result": None,
        "page": "🏠 Home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_session()


def _store_nfa(nfa: NFA) -> None:
    st.session_state["nfa"] = nfa
    st.session_state["conversion_result"] = None  # Invalidate old result


def _get_nfa() -> NFA | None:
    return st.session_state.get("nfa")


def _get_conversion() -> ConversionResult | None:
    cr = st.session_state.get("conversion_result")
    nfa = _get_nfa()
    if nfa is None:
        return None
    if cr is None:
        cr = nfa_to_dfa(nfa)
        st.session_state["conversion_result"] = cr
    return cr


# ────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ────────────────────────────────────────────────────────────────────────────

PAGES = [
    "🏠 Home",
    "🔧 NFA Builder",
    "📊 NFA Visualization",
    "🔄 Conversion Process",
    "📋 DFA Transition Table",
    "📊 DFA Visualization",
    "🧪 String Testing",
]

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 16px 0 24px 0;">
          <div style="font-size:2.4rem;">⚙️</div>
          <div style="font-size:1.2rem; font-weight:700; color:#38bdf8;">NFA → DFA</div>
          <div style="font-size:0.78rem; color:#64748b; margin-top:2px;">Subset Construction Simulator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.session_state["page"] = page

    st.divider()

    nfa_loaded = _get_nfa() is not None
    status_icon = "✅" if nfa_loaded else "⚠️"
    status_text = "NFA Loaded" if nfa_loaded else "No NFA Loaded"
    status_color = "#4ade80" if nfa_loaded else "#fbbf24"

    st.markdown(
        f"""
        <div style="background:#1e293b; border-radius:8px; padding:10px 14px;
                    border:1px solid #334155; text-align:center;">
          <span style="font-size:1.2rem;">{status_icon}</span>
          <span style="color:{status_color}; font-weight:600; margin-left:6px;">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nfa_loaded:
        nfa_preview = _get_nfa()
        st.markdown(
            f"""
            <div style="margin-top:10px; font-size:0.8rem; color:#94a3b8; line-height:1.7;">
              <b>States:</b> {sorted(nfa_preview.states)}<br>
              <b>Alphabet:</b> {sorted(nfa_preview.alphabet)}<br>
              <b>Initial:</b> {nfa_preview.initial_state}<br>
              <b>Finals:</b> {sorted(nfa_preview.final_states)}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# Helper: render graphviz safely
# ────────────────────────────────────────────────────────────────────────────

def _show_graph(dot, caption: str = "") -> None:
    try:
        svg = dot.pipe(format="svg").decode("utf-8")
        st.markdown(
            f'<div style="background:#0f172a; border:1px solid #334155; '
            f'border-radius:12px; padding:20px; overflow-x:auto;">{svg}</div>',
            unsafe_allow_html=True,
        )
        if caption:
            st.caption(caption)
    except Exception as e:
        st.error(f"Graph rendering failed: {e}. Make sure Graphviz is installed.")


# ────────────────────────────────────────────────────────────────────────────
# Page: Home
# ────────────────────────────────────────────────────────────────────────────

def page_home() -> None:
    st.markdown(
        """
        <div class="section-header">
          <h1>⚙️ NFA → DFA Simulator</h1>
          <p>An interactive educational tool for understanding the Subset Construction Algorithm</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """<div class="info-card">
              <div style="font-size:1.8rem; margin-bottom:8px;">🎯</div>
              <div style="font-weight:600; color:#38bdf8; margin-bottom:6px;">What is an NFA?</div>
              <div style="font-size:0.88rem; color:#94a3b8;">
                A <b>Non-Deterministic Finite Automaton</b> can be in multiple states
                simultaneously and may have ε-transitions (moves without consuming input).
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="info-card">
              <div style="font-size:1.8rem; margin-bottom:8px;">🔄</div>
              <div style="font-weight:600; color:#22d3ee; margin-bottom:6px;">Subset Construction</div>
              <div style="font-size:0.88rem; color:#94a3b8;">
                Converts any NFA to an equivalent DFA by treating each <b>set of NFA states</b>
                as a single DFA state. Every NFA has an equivalent DFA.
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="info-card">
              <div style="font-size:1.8rem; margin-bottom:8px;">✅</div>
              <div style="font-weight:600; color:#4ade80; margin-bottom:6px;">What is a DFA?</div>
              <div style="font-size:0.88rem; color:#94a3b8;">
                A <b>Deterministic Finite Automaton</b> has exactly one transition per state
                per symbol. Simpler to implement, easier to reason about.
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### 📚 Glossary of Key Terms")
    terms = {
        "Q (States)": "The finite set of all states in the automaton.",
        "Σ (Alphabet)": "The finite set of input symbols (e.g., {a, b} or {0, 1}).",
        "δ (Transition)": "The transition function mapping (state, symbol) → {states}.",
        "q₀ (Initial State)": "The unique state where computation begins.",
        "F (Final States)": "States that indicate acceptance when computation ends there.",
        "ε-closure": "All states reachable from a set via zero or more ε-transitions.",
        "move(S, a)": "States reachable from set S consuming exactly one symbol a.",
        "Dead State (∅)": "A trap state with no outgoing accepting paths — any input loops here.",
    }
    g1, g2 = st.columns(2)
    items = list(terms.items())
    for i, (term, defn) in enumerate(items):
        col = g1 if i % 2 == 0 else g2
        with col:
            st.markdown(
                f"""<div class="info-card" style="margin-bottom:10px;">
                  <span style="color:#38bdf8; font-weight:600;">{term}</span>
                  <div style="font-size:0.86rem; color:#94a3b8; margin-top:4px;">{defn}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("### 🚀 Quick Start")
    st.markdown(
        """
        1. Go to **🔧 NFA Builder** to define your NFA manually or load a prebuilt example.
        2. Jump to **📊 NFA Visualization** to see your automaton as a graph.
        3. Visit **🔄 Conversion Process** to watch the Subset Construction step-by-step.
        4. Check the **📋 DFA Transition Table** and **📊 DFA Visualization**.
        5. Test strings in **🧪 String Testing** to verify NFA ↔ DFA equivalence.
        """
    )

    st.markdown("### 📖 The Algorithm at a Glance")
    st.markdown(
        """
        ```
        Input:  NFA = (Q, Σ, δ, q0, F)
        Output: DFA = (Q', Σ, δ', q0', F')

        1. q0' ← ε-closure({q0})
        2. worklist ← [q0']
        3. while worklist not empty:
               S ← worklist.pop()
               for each a in Σ:
                   T ← ε-closure( move(S, a) )
                   δ'(S, a) ← T
                   if T not already in Q':
                       add T to Q' and worklist
        4. F' ← { S ∈ Q' | S ∩ F ≠ ∅ }
        ```
        """
    )


# ────────────────────────────────────────────────────────────────────────────
# Page: NFA Builder
# ────────────────────────────────────────────────────────────────────────────

def page_nfa_builder() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>🔧 NFA Builder</h1>
          <p>Define your NFA manually or load a prebuilt example</p>
        </div>""",
        unsafe_allow_html=True,
    )

    build_tab, example_tab, table_tab = st.tabs(
        ["✍️ Manual Definition", "📚 Preloaded Examples", "📄 Transition Table"]
    )

    # ── Manual tab ─────────────────────────────────────────────────────────
    with build_tab:
        st.markdown("#### Step 1 — Define States and Alphabet")
        col1, col2 = st.columns(2)

        with col1:
            raw_states = st.text_input(
                "States (Q) — comma-separated",
                value="q0, q1, q2",
                key="manual_states",
                help="Enter state names separated by commas, e.g.  q0, q1, q2",
            )
        with col2:
            raw_alphabet = st.text_input(
                "Input Alphabet (Σ) — comma-separated, no ε",
                value="a, b",
                key="manual_alphabet",
                help="Enter symbols separated by commas. Do NOT include ε here.",
            )

        col3, col4 = st.columns(2)
        with col3:
            states_list = [s.strip() for s in raw_states.split(",") if s.strip()]
            initial = st.selectbox(
                "Initial State (q₀)",
                options=states_list if states_list else ["—"],
                key="manual_initial",
            )
        with col4:
            final_states = st.multiselect(
                "Final / Accepting States (F)",
                options=states_list,
                key="manual_finals",
            )

        st.markdown("#### Step 2 — Define Transitions")
        st.markdown(
            """<div class="info-card" style="font-size:0.85rem; color:#94a3b8;">
              Enter each transition as: &nbsp;
              <span class="mono" style="color:#38bdf8;">from_state, symbol, to_state1 to_state2 ...</span><br>
              Use <span class="mono" style="color:#22d3ee;">ε</span> or <span class="mono" style="color:#22d3ee;">eps</span>
              as the symbol for epsilon transitions.<br>
              Example: &nbsp; <span class="mono">q0, a, q1 q2</span> &nbsp;→ δ(q0, a) = {q1, q2}
            </div>""",
            unsafe_allow_html=True,
        )

        raw_transitions = st.text_area(
            "Transitions (one per line)",
            value="q0, a, q0 q1\nq0, b, q0\nq1, b, q2",
            height=180,
            key="manual_transitions",
        )

        if st.button("🚀 Build NFA", key="build_manual_btn", use_container_width=True):
            _build_manual_nfa(
                raw_states, raw_alphabet, initial, final_states, raw_transitions
            )

    # ── Examples tab ───────────────────────────────────────────────────────
    with example_tab:
        st.markdown("#### Choose a Preloaded Example")
        example_name = st.selectbox(
            "Example",
            list(EXAMPLES.keys()),
            key="example_select",
            label_visibility="collapsed",
        )
        example = EXAMPLES[example_name]

        st.markdown(
            f"""<div class="info-card">
              <div style="font-weight:600; color:#38bdf8; margin-bottom:8px;">{example_name}</div>
              <div style="font-size:0.88rem; color:#94a3b8;">{example["description"]}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Accepted strings:**")
            for s in example["accepts"]:
                st.code(repr(s), language=None)
        with c2:
            st.markdown("**❌ Rejected strings:**")
            for s in example["rejects"]:
                st.code(repr(s), language=None)

        if st.button("📥 Load This Example", key="load_example_btn", use_container_width=True):
            nfa = get_example(example_name)
            _store_nfa(nfa)
            st.success(f"✅ Loaded: **{example_name}**")
            st.balloons()

    # ── Transition table tab ───────────────────────────────────────────────
    with table_tab:
        st.markdown("#### Enter NFA as a Transition Table")
        st.info(
            "Paste your NFA definition as JSON. This format mirrors the internal "
            "representation and is useful for exact specification.",
            icon="💡",
        )

        json_default = json.dumps(
            {
                "states": ["q0", "q1", "q2"],
                "alphabet": ["a", "b"],
                "initial_state": "q0",
                "final_states": ["q2"],
                "transitions": {
                    "q0": {"a": ["q0", "q1"], "b": ["q0"]},
                    "q1": {"b": ["q2"]},
                },
            },
            indent=2,
        )

        json_input = st.text_area(
            "NFA JSON Definition",
            value=json_default,
            height=280,
            key="json_input",
        )

        if st.button("📥 Import from JSON", key="import_json_btn", use_container_width=True):
            try:
                data = json.loads(json_input)
                nfa = NFA.from_dict(data)
                v = validate_automaton(nfa)
                if v.is_valid:
                    _store_nfa(nfa)
                    st.success("✅ NFA loaded successfully!")
                    if v.warnings:
                        for w in v.warnings:
                            st.warning(w)
                else:
                    for err in v.errors:
                        st.error(err)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
            except Exception as e:
                st.error(f"Error loading NFA: {e}")

    # ── Show current NFA ───────────────────────────────────────────────────
    nfa = _get_nfa()
    if nfa:
        st.divider()
        st.markdown("### 📋 Current NFA Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("States", len(nfa.states))
        c2.metric("Alphabet", len(nfa.alphabet))
        c3.metric("Final States", len(nfa.final_states))
        has_eps = nfa.has_epsilon_transitions()
        c4.metric("ε-transitions", "Yes" if has_eps else "No")

        st.markdown("**Transition Function:**")
        _show_transition_table_nfa(nfa)


def _build_manual_nfa(
    raw_states: str,
    raw_alphabet: str,
    initial: str,
    final_states: list[str],
    raw_transitions: str,
) -> None:
    """Parse manual input and store the NFA."""
    states = {s.strip() for s in raw_states.split(",") if s.strip()}
    alphabet = {a.strip() for a in raw_alphabet.split(",") if a.strip()}

    nfa = NFA(
        states=states,
        alphabet=alphabet,
        initial_state=initial,
        final_states=set(final_states),
    )

    errors = []
    for line in raw_transitions.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",", 2)]
        if len(parts) < 3:
            errors.append(f"Invalid transition line: '{line}' (expected: from, symbol, to...)")
            continue
        src, sym, to_raw = parts
        sym = EPSILON if sym.lower() in ("ε", "eps", "epsilon") else sym
        to_states = {t.strip() for t in to_raw.split() if t.strip()}
        nfa.add_transition(src, sym, to_states)

    if errors:
        for e in errors:
            st.error(e)
        return

    v = validate_automaton(nfa)
    if v.is_valid:
        _store_nfa(nfa)
        st.success("✅ NFA built successfully!")
        if v.warnings:
            for w in v.warnings:
                st.warning(w)
    else:
        for e in v.errors:
            st.error(e)


def _show_transition_table_nfa(nfa: NFA) -> None:
    """Display a nicely formatted NFA transition table."""
    import pandas as pd

    symbols = sorted(nfa.alphabet) + ([EPSILON] if nfa.has_epsilon_transitions() else [])
    rows = []
    for state in sorted(nfa.states):
        row = {
            "State": ("→ " if state == nfa.initial_state else "  ") + state
            + (" *" if state in nfa.final_states else ""),
        }
        for sym in symbols:
            dests = nfa.transitions.get(state, {}).get(sym, set())
            row[sym] = "{" + ", ".join(sorted(dests)) + "}" if dests else "—"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("→ = initial state,  * = accepting state")


# ────────────────────────────────────────────────────────────────────────────
# Page: NFA Visualization
# ────────────────────────────────────────────────────────────────────────────

def page_nfa_viz() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>📊 NFA Visualization</h1>
          <p>Visual representation of your Non-Deterministic Finite Automaton</p>
        </div>""",
        unsafe_allow_html=True,
    )

    nfa = _get_nfa()
    if nfa is None:
        st.info("👋 No NFA loaded yet. Go to **🔧 NFA Builder** first.", icon="💡")
        return

    col_info, col_graph = st.columns([1, 2])

    with col_info:
        st.markdown("#### Legend")
        st.markdown(
            """<div class="info-card" style="font-size:0.86rem;">
              <div>🟢 <b>Green arrow</b> — start / initial state</div>
              <div style="margin-top:6px;">⭕ <b>Double circle</b> — accepting state</div>
              <div style="margin-top:6px;">⭕ <b>Single circle</b> — non-accepting state</div>
              <div style="margin-top:6px;">🔵 <b>Blue edges</b> — regular transitions</div>
              <div style="margin-top:6px;">ε &nbsp;<b>ε labels</b> — epsilon transitions</div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("#### NFA Details")
        st.markdown(
            f"""<div class="info-card" style="font-size:0.85rem; line-height:2.0;">
              <b>Q</b> = {{ {", ".join(sorted(nfa.states))} }}<br>
              <b>Σ</b> = {{ {", ".join(sorted(nfa.alphabet))} }}<br>
              <b>q₀</b> = {nfa.initial_state}<br>
              <b>F</b> = {{ {", ".join(sorted(nfa.final_states)) or "∅"} }}<br>
              <b>ε-trans?</b> {"Yes" if nfa.has_epsilon_transitions() else "No"}
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("#### ε-Closure Table")
        from automata.conversion import epsilon_closure as eps_close
        for state in sorted(nfa.states):
            cl = eps_close({state}, nfa.transitions)
            cl_str = "{" + ", ".join(sorted(cl)) + "}"
            st.markdown(
                f"""<div style="font-size:0.82rem; margin-bottom:4px;">
                  <span class="mono" style="color:#38bdf8;">ε-closure({{{state}}})</span>
                  = <span class="mono" style="color:#4ade80;">{cl_str}</span>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_graph:
        st.markdown("#### Automaton Diagram")
        dot = render_nfa(nfa)
        _show_graph(dot, "NFA — arrows show all possible transitions including ε")


# ────────────────────────────────────────────────────────────────────────────
# Page: Conversion Process
# ────────────────────────────────────────────────────────────────────────────

def page_conversion() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>🔄 Conversion Process</h1>
          <p>Step-by-step Subset Construction (NFA → DFA)</p>
        </div>""",
        unsafe_allow_html=True,
    )

    nfa = _get_nfa()
    if nfa is None:
        st.info("👋 No NFA loaded yet. Go to **🔧 NFA Builder** first.", icon="💡")
        return

    result = _get_conversion()
    dfa = result.dfa

    # ── Summary metrics ───────────────────────────────────────────────────
    st.markdown(
        f"""<div class="metric-row">
          <div class="metric-tile">
            <div class="val">{len(nfa.states)}</div>
            <div class="lbl">NFA States</div>
          </div>
          <div class="metric-tile">
            <div class="val">{len(dfa.states)}</div>
            <div class="lbl">DFA States</div>
          </div>
          <div class="metric-tile">
            <div class="val">{len(dfa.final_states)}</div>
            <div class="lbl">DFA Final States</div>
          </div>
          <div class="metric-tile">
            <div class="val">{len(result.steps)}</div>
            <div class="lbl">Computation Steps</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── ε-closure table ───────────────────────────────────────────────────
    with st.expander("📊 ε-Closure Table (per NFA state)", expanded=False):
        st.markdown(
            "The ε-closure of a state is the set of states reachable by following "
            "**zero or more** ε-transitions (including the state itself)."
        )
        for state, closure in sorted(result.epsilon_closures.items()):
            cl_str = "{" + ", ".join(sorted(closure)) + "}"
            st.markdown(
                f"""<div class="step-card">
                  <span class="mono" style="color:#38bdf8;">ε-closure({{{state}}})</span>
                  &nbsp;=&nbsp;
                  <span class="mono" style="color:#4ade80; font-size:1.05rem;">{cl_str}</span>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Initial state derivation ──────────────────────────────────────────
    init_str = "{" + ", ".join(sorted(dfa.initial_state)) + "}" if dfa.initial_state else "∅"
    st.markdown(
        f"""<div class="info-card">
          <b>DFA Start State</b> = ε-closure({{{nfa.initial_state}}}) =
          <span class="mono" style="color:#4ade80; font-size:1.1rem;">{init_str}</span>
          {"✅ (Accepting)" if dfa.initial_state in dfa.final_states else ""}
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🔍 Step-by-Step Transitions")
    st.markdown(
        "Each row below shows one computation of the Subset Construction loop."
    )

    # Group steps by DFA state for clarity
    from itertools import groupby
    groups: dict = {}
    for step in result.steps:
        key = step.dfa_state
        groups.setdefault(key, []).append(step)

    for dfa_state, steps in groups.items():
        state_str = "{" + ", ".join(sorted(dfa_state)) + "}" if dfa_state else "∅"
        is_final = dfa_state in dfa.final_states
        is_initial = dfa_state == dfa.initial_state
        badges = []
        if is_initial:
            badges.append(
                '<span style="background:#1e3a5f; color:#38bdf8; border-radius:4px; '
                'padding:2px 8px; font-size:0.75rem; margin-left:8px;">INITIAL</span>'
            )
        if is_final:
            badges.append(
                '<span style="background:#14532d; color:#4ade80; border-radius:4px; '
                'padding:2px 8px; font-size:0.75rem; margin-left:8px;">ACCEPTING</span>'
            )

        with st.expander(
            f"DFA State: {state_str}  {'★' if is_final else ''}",
            expanded=(dfa_state == dfa.initial_state),
        ):
            st.markdown(
                f'<div style="margin-bottom:12px;">DFA State: '
                f'<span class="mono" style="color:#38bdf8; font-size:1.1rem;">{state_str}</span>'
                f'{"".join(badges)}</div>',
                unsafe_allow_html=True,
            )

            for step in steps:
                move_str = step.move_result_str
                closure_str = step.closure_result_str
                is_new = step.is_new_state

                st.markdown(
                    f"""<div class="step-card">
                      <div style="margin-bottom:6px;">
                        <span style="color:#94a3b8;">Processing symbol</span>
                        <span class="mono" style="color:#fbbf24; font-size:1.1rem; margin-left:6px;">'{step.symbol}'</span>
                      </div>
                      <div style="margin-bottom:4px;">
                        <span style="color:#94a3b8;">move({state_str}, {step.symbol})</span>
                        &nbsp;=&nbsp;
                        <span class="mono" style="color:#a78bfa;">{move_str}</span>
                      </div>
                      <div style="margin-bottom:4px;">
                        <span style="color:#94a3b8;">ε-closure({move_str})</span>
                        &nbsp;=&nbsp;
                        <span class="mono" style="color:#4ade80;">{closure_str}</span>
                      </div>
                      <div style="font-weight:600; border-top:1px solid #334155; padding-top:6px; margin-top:6px;">
                        δ'({state_str}, {step.symbol}) =
                        <span class="mono" style="color:#38bdf8;">{closure_str}</span>
                        {' &nbsp; <span style="color:#fbbf24; font-size:0.8rem;">← NEW STATE</span>' if is_new else ""}
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )


# ────────────────────────────────────────────────────────────────────────────
# Page: DFA Transition Table
# ────────────────────────────────────────────────────────────────────────────

def page_dfa_table() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>📋 DFA Transition Table</h1>
          <p>Complete transition table of the constructed DFA</p>
        </div>""",
        unsafe_allow_html=True,
    )

    nfa = _get_nfa()
    if nfa is None:
        st.info("👋 No NFA loaded yet. Go to **🔧 NFA Builder** first.", icon="💡")
        return

    result = _get_conversion()
    dfa = result.dfa

    import pandas as pd

    rows = dfa.get_transition_table()
    df = pd.DataFrame(rows)

    # Reorder: DFA State, alphabet symbols, Is Accepting
    sym_cols = sorted(nfa.alphabet)
    show_cols = ["DFA State"] + sym_cols + ["Is Accepting", "Is Initial"]
    df = df[[c for c in show_cols if c in df.columns]]

    # Rename bool columns
    df["Accepting?"] = df["Is Accepting"].map({True: "✅ Yes", False: "❌ No"})
    df["Start?"] = df["Is Initial"].map({True: "→", False: ""})
    df = df.drop(columns=["Is Accepting", "Is Initial"])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
        "Each row represents one DFA state (a subset of NFA states). "
        "∅ = dead/trap state."
    )

    # ── CSV download ─────────────────────────────────────────────────────
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        label="⬇️ Download as CSV",
        data=buf.getvalue(),
        file_name="dfa_transition_table.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ── Accepting states summary ──────────────────────────────────────────
    if dfa.final_states:
        st.markdown("#### ✅ Accepting DFA States")
        for fs in sorted(dfa.final_states, key=lambda s: sorted(s)):
            nfa_subset = "{" + ", ".join(sorted(fs)) + "}" if fs else "∅"
            nfa_finals_in = sorted(fs & nfa.final_states)
            st.markdown(
                f"""<div class="info-card">
                  <span class="mono" style="color:#4ade80;">{nfa_subset}</span>
                  &nbsp;is accepting because it contains NFA final state(s):&nbsp;
                  <span class="mono" style="color:#fbbf24;">{nfa_finals_in}</span>
                </div>""",
                unsafe_allow_html=True,
            )


# ────────────────────────────────────────────────────────────────────────────
# Page: DFA Visualization
# ────────────────────────────────────────────────────────────────────────────

def page_dfa_viz() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>📊 DFA Visualization</h1>
          <p>Visual representation of the constructed DFA</p>
        </div>""",
        unsafe_allow_html=True,
    )

    nfa = _get_nfa()
    if nfa is None:
        st.info("👋 No NFA loaded yet. Go to **🔧 NFA Builder** first.", icon="💡")
        return

    result = _get_conversion()
    dfa = result.dfa

    col_info, col_graph = st.columns([1, 2])

    with col_info:
        st.markdown("#### DFA Summary")
        st.markdown(
            f"""<div class="info-card" style="font-size:0.85rem; line-height:2.0;">
              <b>|Q'|</b> = {len(dfa.states)} states<br>
              <b>Σ</b> = {{ {", ".join(sorted(dfa.alphabet))} }}<br>
              <b>Initial:</b> {{ {", ".join(sorted(dfa.initial_state))} }}<br>
              <b>|F'|</b> = {len(dfa.final_states)} accepting state(s)
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("#### DFA States")
        for state in sorted(dfa.states, key=lambda s: sorted(s)):
            label = dfa.format_state(state)
            is_init = state == dfa.initial_state
            is_final = state in dfa.final_states
            icon = "★ " if is_final else "  "
            arrow = "→ " if is_init else "  "
            color = "#4ade80" if is_final else "#38bdf8" if is_init else "#94a3b8"
            st.markdown(
                f'<div style="font-size:0.83rem; margin-bottom:3px; color:{color};">'
                f'{arrow}{icon}<span class="mono">{label}</span></div>',
                unsafe_allow_html=True,
            )
        st.caption("→ initial  |  ★ accepting")

    with col_graph:
        st.markdown("#### Automaton Diagram")
        dot = render_dfa(dfa)
        _show_graph(
            dot,
            "DFA — each node shows the NFA subset it represents; "
            "red node = dead/trap state (∅)",
        )


# ────────────────────────────────────────────────────────────────────────────
# Page: String Testing
# ────────────────────────────────────────────────────────────────────────────

def page_string_testing() -> None:
    st.markdown(
        """<div class="section-header">
          <h1>🧪 String Testing</h1>
          <p>Test strings against both the NFA and the constructed DFA</p>
        </div>""",
        unsafe_allow_html=True,
    )

    nfa = _get_nfa()
    if nfa is None:
        st.info("👋 No NFA loaded yet. Go to **🔧 NFA Builder** first.", icon="💡")
        return

    result = _get_conversion()
    dfa = result.dfa

    st.markdown(
        f"""<div class="info-card" style="font-size:0.86rem;">
          <b>Alphabet:</b> {{ {", ".join(sorted(nfa.alphabet))} }}&emsp;
          <b>Initial:</b> {nfa.initial_state}&emsp;
          <b>Finals:</b> {{ {", ".join(sorted(nfa.final_states))} }}
        </div>""",
        unsafe_allow_html=True,
    )

    input_str = st.text_input(
        "Input String (leave blank for ε — the empty string)",
        value="",
        key="test_string_input",
        placeholder="e.g. aba or 0101",
    )

    col_run, col_batch = st.columns([1, 1])
    with col_run:
        run_single = st.button("▶️ Test This String", use_container_width=True)
    with col_batch:
        run_batch = st.button("⚡ Run All Example Strings", use_container_width=True)

    if run_single:
        _run_single_test(nfa, dfa, input_str)

    if run_batch:
        # Determine which example is loaded
        _run_batch_test(nfa, dfa)


def _verdict_badge(accepted: bool) -> str:
    if accepted:
        return '<span class="badge-accept">ACCEPTED ✅</span>'
    return '<span class="badge-reject">REJECTED ❌</span>'


def _run_single_test(nfa: NFA, dfa, input_str: str) -> None:
    display_str = repr(input_str) if input_str else "ε (empty string)"
    st.markdown(f"### Results for: `{display_str}`")

    nfa_sim = simulate_nfa(nfa, input_str)
    dfa_sim = simulate_dfa(dfa, input_str)
    equivalent = nfa_sim.accepted == dfa_sim.accepted

    col_nfa, col_dfa = st.columns(2)

    with col_nfa:
        st.markdown("#### NFA Simulation")
        st.markdown(_verdict_badge(nfa_sim.accepted), unsafe_allow_html=True)
        if not nfa_sim.accepted and nfa_sim.rejection_reason:
            st.caption(f"Reason: {nfa_sim.rejection_reason}")

        st.markdown("**Active States per Step:**")
        for step in nfa_sim.steps:
            sym_label = step.symbol if step.symbol is not None else "ε-closure(q₀)"
            states_str = (
                "{" + ", ".join(sorted(step.active_states)) + "}"
                if step.active_states
                else "∅"
            )
            st.markdown(
                f"""<div class="step-card">
                  <span style="color:#94a3b8;">after </span>
                  <span class="mono" style="color:#fbbf24;">'{sym_label}'</span>
                  <span style="color:#94a3b8;"> → </span>
                  <span class="mono" style="color:#38bdf8;">{states_str}</span>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_dfa:
        st.markdown("#### DFA Simulation")
        st.markdown(_verdict_badge(dfa_sim.accepted), unsafe_allow_html=True)
        if not dfa_sim.accepted and dfa_sim.rejection_reason:
            st.caption(f"Reason: {dfa_sim.rejection_reason}")

        st.markdown("**State Sequence:**")
        for step in dfa_sim.steps:
            sym_label = step.symbol if step.symbol is not None else "start"
            state_str = (
                "{" + ", ".join(sorted(step.current_state)) + "}"
                if step.current_state
                else "∅"
            )
            is_final = step.current_state in dfa.final_states
            st.markdown(
                f"""<div class="step-card">
                  <span style="color:#94a3b8;">after </span>
                  <span class="mono" style="color:#fbbf24;">'{sym_label}'</span>
                  <span style="color:#94a3b8;"> → </span>
                  <span class="mono" style="color:#38bdf8;">{state_str}</span>
                  {"&ensp;✅" if is_final else ""}
                </div>""",
                unsafe_allow_html=True,
            )

    # Equivalence check
    eq_color = "#4ade80" if equivalent else "#fb7185"
    eq_text = "Verified ✅" if equivalent else "MISMATCH ❌"
    st.markdown(
        f"""<div class="info-card" style="text-align:center; margin-top:16px;">
          <span style="color:#94a3b8; font-size:0.9rem;">NFA ↔ DFA Equivalence: </span>
          <span style="color:{eq_color}; font-weight:700; font-size:1.1rem;">{eq_text}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def _run_batch_test(nfa: NFA, dfa) -> None:
    """Try strings from the preloaded examples that match this NFA."""
    st.markdown("### ⚡ Batch Test Results")

    # Collect test strings from all examples that match this NFA's alphabet
    test_strings = set()
    for ex in EXAMPLES.values():
        ex_alpha = set(ex["data"]["alphabet"])
        if ex_alpha == nfa.alphabet or ex_alpha.issubset(nfa.alphabet):
            test_strings.update(ex["accepts"] + ex["rejects"])
    # Also include some systematic short strings
    import itertools
    for length in range(0, 5):
        for combo in itertools.product(sorted(nfa.alphabet), repeat=length):
            test_strings.add("".join(combo))

    rows = []
    mismatches = 0
    for s in sorted(test_strings, key=lambda x: (len(x), x))[:50]:
        nfa_r = simulate_nfa(nfa, s)
        dfa_r = simulate_dfa(dfa, s)
        match = nfa_r.accepted == dfa_r.accepted
        if not match:
            mismatches += 1
        rows.append({
            "String": repr(s) if s else "ε",
            "NFA": "✅" if nfa_r.accepted else "❌",
            "DFA": "✅" if dfa_r.accepted else "❌",
            "Equivalent?": "✅" if match else "🚨 MISMATCH",
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if mismatches == 0:
        st.success(
            f"✅ All {len(rows)} tested strings produce identical results on NFA and DFA. "
            "Mathematical equivalence confirmed!",
            icon="🎉",
        )
    else:
        st.error(
            f"🚨 {mismatches} mismatch(es) found! The conversion may have a bug.",
        )


# ────────────────────────────────────────────────────────────────────────────
# Router
# ────────────────────────────────────────────────────────────────────────────

page = st.session_state.get("page", "🏠 Home")

if page == "🏠 Home":
    page_home()
elif page == "🔧 NFA Builder":
    page_nfa_builder()
elif page == "📊 NFA Visualization":
    page_nfa_viz()
elif page == "🔄 Conversion Process":
    page_conversion()
elif page == "📋 DFA Transition Table":
    page_dfa_table()
elif page == "📊 DFA Visualization":
    page_dfa_viz()
elif page == "🧪 String Testing":
    page_string_testing()
