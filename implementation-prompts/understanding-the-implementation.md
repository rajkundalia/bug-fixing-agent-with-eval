Viewed run_harness.py:1-48

Good starting point — `run_harness.py` is actually the right file to read first since it's the entry point that wires everything together. Here's the recommended reading order:

---

## Reading Order

### 1. `run_harness.py` ← you're here
The top of the call stack. Understand what it orchestrates before diving into the pieces. Read it end-to-end — it calls `resolve_issue()`, then all the evaluators, then saves results.

### 2. `agents/tools.py`
Tiny file (3 functions). This is the entire tool surface the agent can call: `read_file`, `edit_file`, `run_tests`. Read this before the agent loop — you need to know what tools exist before understanding how they're dispatched.

### 3. `agents/issue_resolver.py`
The agent loop. Understand how Ollama's `chat()` works with `tools=[]`, how each turn is logged into the trace, and why the **trace dict is the central artifact** everything else reads from.

### 4. `src/calculator.py` + `tests/test_calculator.py`
Pick one broken source file and its test together. This makes the "what the agent is actually fixing" concrete before you read the evaluators. The `# BUG:` comments show exactly what's broken.

### 5. `evals/outcome.py`
Simplest evaluator — just checks the last `run_tests` result in the trace. Read this to understand the **trace schema** (what shape the data is in when evaluators receive it).

### 6. `evals/tool_correctness.py` → `evals/tool_flow.py` → `evals/trajectory.py`
Three rule-based evaluators in increasing complexity. All read from the same trace.

### 7. `judges/llm_judge.py`
The LLM judge. Read the two prompt templates (`TASK_COMPLETION_PROMPT`, `FIX_QUALITY_PROMPT`) — these encode the rubrics for the two "fuzzy" evals.

### 8. `evals/task_completion.py` + `evals/fix_quality.py`
Thin wrappers that call the judge. After reading `llm_judge.py` these are trivial.

### 9. `configs/config_baseline.json` vs `configs/config_no_run_tests.json`
Read side by side. The only difference is `run_tests` being absent from the tools list. This is the key experiment.

### 10. `reports/compare_configs.py`
The payoff — how results from two configs get diffed to produce the headline finding.

---

**Mental model in one line:**  
`run_harness.py` → `issue_resolver.py` produces a **trace** → all `evals/` read that trace → `compare_configs.py` diffs eval results across configs.