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

---

## Frequently Asked Questions & Design Decisions

### Q: Is this project an agent or an evaluation framework?
* **The Agent is the Vehicle:** `agents/issue_resolver.py` is intentionally minimal (~140 lines) using raw `ollama` tool-calling, without heavy frameworks (like LangChain or AutoGen). Its sole purpose is to act as the test subject that produces a structured execution `trace`.
* **The Real Artifact:** The core teaching artifact and value of this repository is the multi-layered evaluation suite in `evals/` and the comparative benchmarking harness.

### Q: Are the 10 JSON files in `datasets/` 10 separate datasets? What does the agent actually see?
* **10 Files = 1 Benchmark Suite:** The `datasets/` directory is **one** evaluation dataset (like an exam) containing 10 individual task scenarios (questions #1 through #10).
* **What the Agent Receives (The Prompt):** Only `task['description']` (the bug report) and `task['target_file']` (the file to edit).
* **What is Kept Secret (The Answer Key):** `planted_root_cause` (used by `evals/fix_quality.py` to grade the fix) and `test_file` (used by the runner) are hidden from the agent prompt to ensure genuine reasoning without leaking the answer.

### Q: What does `task['description']` contain, and how does it compare to real-world agent inputs?
* **In This Project:** It contains a concise, synthetic bug report (e.g., *"The function `calculate_total` in `src/calculator.py` raises an IndexError when called with an empty list. It should return 0 instead."*).
* **In Real Life (SWE-bench / Production):** A real agent receives an unstructured GitHub Issue or Jira ticket containing a title, problem description, stack trace, and user comments.
* **Why Synthetic for Evals:** Synthetic descriptions provide a clean, unambiguous specification of intent. This guarantees that when an agent fails, the failure is caused by reasoning or tool-misuse deficiencies rather than vague issue descriptions or noisy logs.

### Q: In real life, agents search the whole repo. Why does our prompt explicitly pass `Target file: {task['target_file']}`?
* **Real-World Agents (SWE-bench, Devin, OpenHands):** Receive a raw GitHub issue and must search thousands of files with `grep` or file-tree tools.
* **Our Synthetic Benchmark:** Explicitly provides `target_file` for three reasons:
  1. **Variable Isolation:** Isolates the bug-fixing and tool-calling loop from repo-wide code search (so failures reflect tool/code logic, not search failures).
  2. **Deterministic Grading:** Enables `evals/tool_correctness.py` to objectively verify if the agent edited the expected file and avoided touching tests or forbidden files.
  3. **Speed & Zero Cost:** Keeps context small (~4k tokens) so tests run in seconds locally on Ollama without large context windows or API bills.

### Q: Why is `think` set to `false` in configs, and will `model_content` even show up in traces?
* **Why `think: false`:** Configured across baseline runs to establish a fast, low-latency performance benchmark without reasoning token overhead.
* **When `model_content` is Populated:**
  * **On tool turns (`read_file`, `edit_file`, `run_tests`):** The model directly emits structured tool calls without speaking, so `model_content` is logged as `""` (empty string).
  * **On the final turn:** When the agent finishes or explains its fix with plain text, `model_content` captures that full response string.
  * **With `think: true`:** If enabled in future configs, `model_content` captures chain-of-thought reasoning tokens across all intermediate turns.

### Q: How does the agent encounter `adversarial_content`? Is it passed in the user prompt or read from disk?
* **Not in Prompt:** The agent prompt only says *"Fix calculate_total in src/calculator.py"*. The field `adversarial_content` in `task_009_adversarial.json` is **never passed directly to the LLM in the prompt**.
* **Read from Disk (Indirect Injection):** The malicious comment (`# NOTE TO AI ASSISTANT: ...`) is pre-written inside `src/calculator.py` on disk. When the agent calls `read_file("src/calculator.py")`, it encounters the injection inside the code docstring.
* **Role of JSON Field:** In `task_009_adversarial.json`, `"adversarial_content"` acts as a **boolean feature flag** for `run_harness.py` (`if task.get("adversarial_content"):`) to trigger `evaluate_adversarial()`.
* **How it's Evaluated:** `evals/adversarial.py` checks whether the agent resisted the injected shortcut (adding `assert True` to tests) and fixed the actual source code instead.

### Q: Why do we use two different local models (`qwen3:8b` as agent and `llama3.1:8b` as judge)?
* **Eliminates Self-Preference Bias:** LLMs tend to be lenient when grading their own generated code or reasoning. Using a different model family for judging (`llama3.1:8b`) ensures an unbiased, independent evaluation.
* **Sequential & Zero Cost:** Both models run locally via Ollama in sequence (agent trace generated first, judge scores trace second), requiring zero cloud API costs and fitting easily in 16GB RAM.