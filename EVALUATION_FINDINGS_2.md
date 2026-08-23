# Empirical Evaluation Findings & Benchmarking Analysis (Run 2 — Extended Metrics)

*Comprehensive empirical findings from the remediated 3-way evaluation benchmark run across `config_baseline`, `config_prompt_v2`, and `config_no_run_tests`.*

---

## 1. Executive Summary

This report documents the empirical results from **Run 2**, incorporating:
- **Diff Persistence**: Passing actual `git diff` output directly to the LLM judge.
- **Unified Evaluation Logic**: Synchronized scoring between inline harness and post-hoc judge.
- **Full Token & Resource Accounting**: Complete tracking of input/output tokens, wall-clock latency, turn counts, and estimated USD cost using standard Anthropic API rates ($1.00 / 1M input, $5.00 / 1M output for `claude-haiku-4-5`).

---

## 2. Benchmark Headline Metrics (Run 1 vs Run 2)

### Run 2 Metrics Table (10 Tasks per Config)

| Metric | `config_baseline` | `config_prompt_v2` | `config_no_run_tests` |
| :--- | :---: | :---: | :---: |
| **Pass Rate (Rule-Based Outcome)** | **7 / 10 (70%)** | **7 / 10 (70%)** | **9 / 10 (90%)** |
| **LLM Judge Completion Score** | **0.80 avg** | **0.80 avg** | **1.00 avg** |
| **Fix Quality (Genuine Fixes)** | **100% Genuine** | **100% Genuine** | **100% Genuine** |
| **Avg Turns per Task** | 3.9 turns | 3.9 turns | 4.0 turns |
| **Avg Latency per Task** | 5.52 sec | 5.83 sec | 6.52 sec |
| **Total Benchmark Tokens** | 46,388 tokens | 47,099 tokens | 45,422 tokens |
| **Total Benchmark Cost (USD)** | **$0.0656** | **$0.0670** | **$0.0699** |
| **Adversarial Safety Rate** | **100% (Passed)** | **100% (Passed)** | **100% (Passed)** |

> **Key Takeaways**:
> - **Blind Execution (`config_no_run_tests`)** achieved the highest task completion score (1.00 avg) and pass rate (90%). Without a test runner tool, the agent focuses single-mindedly on analyzing the source code root cause rather than relying on iterative test trial-and-error.
> - **Latency & Cost Trade-off**: Operating without a test runner resulted in slightly higher wall-clock latency (+1.0s avg) and slightly higher cost ($0.0699 vs $0.0656 total) because turns required more verbose reasoning to compensate for missing feedback.
> - **Prompt Bloat (`config_prompt_v2`)**: Adding rigid step-by-step diagnostic instructions increased token usage (+711 tokens total) and latency (+0.31s/task) without improving task completion or pass rates.

---

## 3. Comparative Analysis across Runs

| Dimension | Run 1 (Original Baseline) | Run 2 (Remediated Run) | Difference & Takeaway |
| :--- | :--- | :--- | :--- |
| **Fix Quality Judge Context** | Inferred from trace log text | Exact `git diff` code changes | Diff persistence provides concrete code edits to judge |
| **Token & Cost Accounting** | Unreported | Full Token & USD Cost breakdown | Cost per run is ~$0.066 - $0.070 across 10 tasks |
| **Judging Logic Consistency** | Separate inline vs post-hoc logic | Unified `run_llm_judge_evals()` | Zero scoring variance between harness & judge |
| **Efficiency Metrics** | Partial (turns & latency only) | Full turns, latency, tokens, & cost | Clear view of efficiency vs accuracy trade-offs |

---

## 4. Key Findings & Behavioral Insights

### Finding 1: The Blind Execution Paradox (`config_no_run_tests`)
* **Observation**: Omitting `run_tests` did not degrade performance — it improved pass rate from 70% to 90%.
* **Mechanism**: When `run_tests` is present, agents often fall into a "guess-and-check" loop (editing code and running tests repeatedly). When `run_tests` is absent, the agent carefully reads both the source code and the test suite in its initial turn, identifying the exact root cause before making a single, precise edit.
* **Cost Impact**: Blind execution uses slightly fewer total tokens (45,422 vs 46,388) but takes 1.0 second longer per task due to heavier reasoning per turn.

### Finding 2: Verbose Prompting Increases Cost Without Improving Accuracy (`config_prompt_v2`)
* **Observation**: Forcing structured step-by-step diagnostic thinking (`config_prompt_v2`) added 711 tokens and increased total benchmark cost from $0.0656 to $0.0670.
* **Mechanism**: The model spent turns summarizing bug reports and detailing diagnostic steps that produced no extra problem-solving value over the concise baseline prompt.

### Finding 3: Turn Budget Boundaries (`task_002` & `task_007`)
* **Observation**: `task_002` and `task_007` persistently fail under tight turn budgets (`max_turns: 3`), but achieve high completion scores when allowed sufficient steps.
* **Lesson**: Evaluation harnesses must carefully distinguish between **agent capability failures** and **harness turn budget constraints**.

### Finding 4: Single-Run ($n=1$) Stochastic Variance (Run 1 vs Run 2 Comparison)
* **Observation**: In Run 1, `config_baseline` achieved 80% (8/10) vs `config_prompt_v2` at 70% (7/10). In Run 2, both configs scored identical 70% pass rates (7/10), because `task_010` flipped from PASS -> FAIL in Baseline and FAIL -> PASS in Prompt V2 due to minor LLM temperature sampling variance.
* **Mechanism**: On a small dataset ($n=10$), a single task state shift causes a 10% swing in headline pass rate.
* **Lesson**: Single-run ($n=1$) benchmarks are essential for fast diagnostic smoke-testing, but small score differences (e.g. 70% vs 80%) should be interpreted as within sampling noise unless verified over multiple trials ($n \ge 3$). This highlights the importance of accounting for statistical variance when benchmarking non-deterministic LLMs.

---

## 5. Artifact References

- **Baseline Run Report (Run 1)**: [`reports/comparison_report_1.md`](reports/comparison_report_1.md)
- **Extended Metrics Report (Run 2)**: [`reports/comparison_report_2.md`](reports/comparison_report_2.md)
