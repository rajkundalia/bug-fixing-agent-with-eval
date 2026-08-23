# Understanding the Implementation & Code Map [ARCHIVED REFERENCE]

> **Note**: Implementation is complete. The active Python codebase (`run_harness.py`, `agents/`, `evals/`, `judges/`) and `README.md` are the primary source of truth.

`run_harness.py` is the entry point that wires everything together. Recommended code reading order:

---

## Reading Order

### 1. `run_harness.py` ← start here
The top of the call stack. Read it end-to-end — it orchestrates tasks, resets repository state (`git checkout`), runs `resolve_issue()`, triggers rule-based evaluators, and saves results.

### 2. `agents/tools.py`
Tiny file (3 functions). This is the entire tool surface the agent can call: `read_file`, `edit_file`, `run_tests` (with optional `path` and `filter` arguments).

### 3. `agents/issue_resolver.py`
The agent loop. Decoupled and data-driven — uses Anthropic Messages API (`claude-haiku-4-5`) with parallel tool execution support and explicit turn labeling `[Turn X.Y] (Parallel)`.

### 4. `src/calculator.py` + `tests/test_calculator.py`
Pick one broken source file and its test together. The `# BUG:` comments show exactly what's broken in the synthetic benchmark suite.

### 5. `evals/outcome.py`
Outcome evaluator — checks recorded test results or triggers a **post-hoc pytest verification** if the agent was executed without a native `run_tests` tool.

### 6. `evals/tool_correctness.py` → `evals/tool_flow.py` → `evals/trajectory.py` → `evals/safety.py`
Five rule-based evaluators in increasing complexity. All read from the same execution trace.

### 7. `run_judge.py` & `judges/llm_judge.py`
The standalone LLM judge powered by `claude-haiku-4-5`. Evaluates traces for **Task Completion** (`COMPLETE`, `PARTIAL`, `FAILED`) and **Fix Quality** (`GENUINE`, `WORKAROUND`, `FAILED`). Run across all benchmark outputs via `uv run python run_judge.py --all`.

### 8. `reports/compare_configs.py`
The payoff — auto-discovers latest evaluation results across configs (`config_baseline` vs `config_prompt_v2` vs `config_no_run_tests`) and generates side-by-side comparative tables saved to `reports/comparison_report.md`.

---

**Mental model in one line:**  
`run_harness.py` → `issue_resolver.py` produces a **trace** → `evals/` and `run_judge.py` score that trace → `compare_configs.py` diffs configs into `comparison_report.md`.

---

## Frequently Asked Questions & Design Decisions

### Q: Is this project an agent or an evaluation framework?
* **The Agent is the Vehicle:** `agents/issue_resolver.py` is intentionally minimal (~170 lines) using direct Anthropic API tool-calling. Its sole purpose is to act as the test subject that produces a structured execution `trace`.
* **The Real Artifact:** The core teaching artifact and value of this repository is the multi-layered evaluation suite in `evals/`, the LLM judge in `judges/`, and the comparative benchmarking harness.

### Q: Are the 10 JSON files in `datasets/` 10 separate datasets? What does the agent actually see?
* **10 Files = 1 Benchmark Suite:** The `datasets/` directory is **one** evaluation dataset containing 10 individual task scenarios.
* **What the Agent Receives (The Prompt):** `task['description']` (the bug report), `task['target_file']` (file to edit), and `task['test_filter']` (specific pytest test filter).
* **What is Kept Secret (The Answer Key):** `planted_root_cause` (used by `judges/llm_judge.py` to grade fix quality) and `test_file` (used by post-hoc test runner) are hidden from the agent prompt to ensure genuine reasoning without leaking the answer.

### Q: How does post-hoc evaluation work for `config_no_run_tests`?
* **The Problem:** When `run_tests` is omitted from the agent's toolset, the agent cannot report test results during execution.
* **The Solution:** `evals/outcome.py` checks if `run_tests` output exists. If missing, it automatically executes a targeted post-hoc `pytest` command against the task's `test_file` and `test_filter`. This guarantees an accurate ground-truth score without false negatives.

### Q: Why does `judges/llm_judge.py` ask for categorical verdicts instead of floating-point scores?
* **Eliminates Calibration Noise:** LLMs struggle with arbitrary continuous floats (`0.65` vs `0.75`). Asking the judge to pick from discrete, mutually exclusive categories (`COMPLETE`, `PARTIAL`, `FAILED` for task completion; `GENUINE`, `WORKAROUND`, `FAILED` for fix quality) produces highly consistent judgments.
* **Deterministic Score Mapping:** Python deterministically converts verdicts to numerical scores (`COMPLETE`/`GENUINE` = 1.0, `PARTIAL`/`WORKAROUND` = 0.5, `FAILED` = 0.0).