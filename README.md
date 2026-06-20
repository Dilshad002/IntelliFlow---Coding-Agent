# IntelliFlow 

**An autonomous coding agent that writes, runs, and fixes its own Python — without a human in the loop.**

IntelliFlow takes a plain-English programming problem, generates code, executes it in a sandboxed subprocess, reads the *real* stdout/stderr, and rewrites itself on failure. Up to 5 attempts. No hand-holding.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Agent-LangGraph-1C3C3C)](https://www.langchain.com/langgraph)
[![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20gpt--oss--120b-F55036)](https://console.groq.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Deployed on Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render&logoColor=white)](https://intelliflow-app.onrender.com)

---

## Demo

**Prompt:** *"write a program that prints prime numbers infinitely"*

```
› Generating code for the first time
› [Attempt 1] Running code...
› Checking the code for errors...
✗ Error: Code execution timed out after 10 seconds...
› [Attempt 2] Running code...
› Checking the code for errors...
✓ Success — 2 attempts
```

The agent detected the infinite loop from the **timeout signal alone** — no static analysis, no hints — rewrote the code to use a bounded generator, and passed on the second try. That's the whole point: it reasons from *execution feedback*, not guesses.

---

## Why This Is Different From "LLM Writes Code"

Most "AI code generator" demos are a single LLM call with no verification loop. IntelliFlow is a **closed-loop agent**:

| Capability | What it means |
|---|---|
| **Self-correction** | Fixes are driven by real stderr/stdout, not re-prompting blindly |
| **Real sandboxing** | Code executes in an isolated subprocess with a hard timeout — not `eval()` |
| **Stateful graph, not a chain** | LangGraph manages conditional branching (retry vs. exit), not a fixed pipeline |
| **Bounded autonomy** | Hard exit at 5 attempts — it doesn't spin forever on unsolvable problems |

---

## Architecture

```
User Input (natural language problem)
        │
        ▼
┌──────────────┐
│  write_code  │  ← LLM generates Python code (Groq API)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   run_code   │  ← Executes in sandboxed subprocess (10s timeout)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   evaluate   │  ← Checks stdout (non-empty) and stderr (empty)
└──────┬───────┘
       │
       ├── success=True  OR  attempts ≥ 5 ──► END
       │
       ▼
┌──────────────┐
│   fix_code   │  ← LLM gets original problem + broken code + error
└──────┬───────┘
       │
       └──────────────────────────────► back to run_code (retry)
```

**Stack**

| Layer | Tech |
|---|---|
| Agent framework | LangGraph |
| LLM | Groq API (`openai/gpt-oss-120b`) |
| Code execution | Python `subprocess`, 10s timeout |
| Backend | FastAPI |
| Frontend | Streamlit |
| Deployment | Render |

---

## Project Structure

```
intelliflow/
├── agent.py        # LangGraph graph, nodes, AgentState
├── executor.py     # Sandboxed subprocess code execution
├── api.py          # FastAPI backend — exposes /run endpoint
├── app.py          # Streamlit frontend
├── .env            # GROQ_API_KEY (not committed)
├── requirements.txt
└── README.md
```

---

## How It Works

### AgentState

Every node reads from and writes to one shared state object:

```python
class AgentState(TypedDict):
    user_prompt: str    # original problem
    code: str           # current code attempt
    output: str         # stdout from execution
    error: str          # stderr from execution
    attempts: int        # retry count
    success: bool        # exit condition
    trace: list          # reasoning steps for UI display
```

### Nodes

| Node | Role |
|---|---|
| `write_code` | Calls Groq LLM with system prompt + user problem, returns Python code only |
| `run_code` | Passes code to `execute_code()`, stores stdout/stderr, increments attempts |
| `evaluate` | Sets `success=True` if stdout is non-empty **and** stderr is empty |
| `fix_code` | Sends problem + broken code + error back to the LLM for correction |

### Exit Conditions

The agent stops when:
- `success == True` — code ran and produced output, **or**
- `attempts >= 5` — max retries exhausted

### Safety

- Code executes in an isolated subprocess, never in the agent's own process
- A 10-second timeout kills hanging or infinite-loop processes
- The LLM is instructed to use Python standard library only — no third-party imports
- stdin is disabled — all examples rely on hardcoded values

> **Note:** the standard-library and stdin constraints are enforced via the system prompt, not sandboxed at the OS/process level. The subprocess isolation and timeout are the actual hard guarantees.

---

## API

**POST** `/run`

**Request**
```json
{
  "user_prompt": "write a function that sorts a list and prints the result"
}
```

**Response**
```json
{
  "code": "def sort_list(lst):\n    ...",
  "output": "[1, 2, 3, 5, 9]\n",
  "error": "",
  "attempts": 1,
  "success": true,
  "trace": [
    "Generating code for the first time",
    "[Attempt 1] Running code...",
    "Checking the code for errors..."
  ]
}
```

---

## Local Setup

**Prerequisites:** Python 3.10+, a free [Groq API key](https://console.groq.com)

```bash
# Clone the repo
git clone https://github.com/Dilshad002/intelliflow
cd intelliflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Terminal 1 — start the API
uvicorn api:app --reload

# Terminal 2 — start the frontend
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## What This Project Demonstrates

- **ReAct pattern** — the agent reasons, acts (executes), observes (reads real output/error), and loops
- **Tool use with real side effects** — the executor is a genuine tool call, not an LLM hallucinating results
- **Self-correction from ground truth** — fixes are driven by actual execution feedback, not re-guessing
- **Agentic architecture** — a LangGraph state graph with conditional edges, not a linear prompt chain
- **Engineering discipline** — sandboxing, timeouts, and bounded retries instead of unconstrained autonomy

---

## Author

**Dilshad** — [GitHub](https://github.com/Dilshad002/intelliflow) · [HuggingFace](https://huggingface.co/dilshad002)