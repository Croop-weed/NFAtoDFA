# NFA → DFA Simulator

An interactive educational tool for understanding the **Subset Construction Algorithm** (NFA → DFA conversion), built with Python and Streamlit.

---

## ✨ Features

| Feature | Description |
|---|---|
| **NFA Builder** | Define NFAs manually, via JSON, or load prebuilt examples |
| **NFA Visualization** | Graphviz diagram with ε-transitions, double-circle accepting states |
| **Step-by-Step Conversion** | Full Subset Construction walkthrough with move() and ε-closure per step |
| **DFA Transition Table** | Auto-generated table with CSV download |
| **DFA Visualization** | DFA graph showing NFA subsets as state labels |
| **String Testing** | Simulate strings on both NFA and DFA; verify equivalence |
| **Batch Testing** | Test all strings up to length N; auto-detect mismatches |
| **4 Preloaded Examples** | Strings ending in 'ba', 'abb', '01', and ε-transition demos |

---

## 🚀 Installation & Running

### Prerequisites

- Python 3.11+
- [Graphviz](https://graphviz.org/download/) system package:
  ```bash
  # Ubuntu / Debian
  sudo apt-get install graphviz

  # macOS
  brew install graphviz

  # Windows
  winget install graphviz
  ```

### Install Python Dependencies

```bash
cd Autometa_Simulator
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output: all tests pass, including:
- `test_nfa.py` — NFA data model tests
- `test_conversion.py` — Subset construction, ε-closure, move(), equivalence
- `test_simulation.py` — NFA and DFA simulation

---

## 📁 Project Structure

```
Autometa_Simulator/
│
├── app.py                    # Streamlit UI (7 pages)
├── requirements.txt
├── README.md
│
├── automata/
│   ├── __init__.py
│   ├── nfa.py                # NFA dataclass
│   ├── dfa.py                # DFA dataclass
│   ├── conversion.py         # Subset construction algorithm
│   ├── simulation.py         # NFA/DFA string simulation
│   └── validation.py         # Input validation
│
├── visualization/
│   ├── __init__.py
│   └── graph.py              # Graphviz rendering
│
├── examples/
│   ├── __init__.py
│   └── sample_nfas.py        # 4 preloaded NFA examples
│
└── tests/
    ├── __init__.py
    ├── test_nfa.py
    ├── test_conversion.py
    └── test_simulation.py
```

---

## 🔢 The Algorithm

The **Subset Construction** (Powerset Construction) algorithm:

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

**Key functions implemented independently (in `automata/conversion.py`):**

- `epsilon_closure(states, transitions)` — states reachable via ε*
- `move(states, symbol, transitions)` — states reached consuming one symbol
- `nfa_to_dfa(nfa)` — full subset construction returning DFA + all steps
- `simulate_nfa(nfa, string)` — NFA simulation (set-of-states)
- `simulate_dfa(dfa, string)` — DFA simulation (single-state tracking)
- `validate_automaton(nfa)` — validates all NFA fields

---

## 📚 Preloaded Examples

| Example | Alphabet | Language |
|---|---|---|
| Strings ending in 'ba' | {a, b} | `(a+b)*ba` |
| Strings containing 'abb' | {a, b} | `(a+b)*abb(a+b)*` |
| ε-transitions demo | {0, 1} | Strings where 2nd-to-last is '1' |
| Strings ending in '01' | {0, 1} | `(0+1)*01` |

---

## 🎓 Educational Design

- Every conversion step shows `move()`, `ε-closure()`, and the resulting DFA transition.
- All DFA states display the corresponding NFA subset.
- String testing shows active states (NFA) or state sequence (DFA) at each symbol.
- Batch testing generates all strings up to length 4 and verifies NFA ↔ DFA equivalence.
- The dead state ∅ is shown in red to indicate no accepting path exists.

---

## 📄 License

MIT License. For educational use.
