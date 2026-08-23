# Benchmark Configuration Comparison Report (Run 2 — Extended Metrics)
*Generated: 2026-08-23 11:26 | Agent Model: `claude-haiku-4-5` | Judge Model: `claude-haiku-4-5`*

## Comparison: config_baseline vs config_prompt_v2

**Summary**: [OK] 1 improvement(s): ['task_010'] | Avg task-completion: 0.8 -> 0.8 (+0.0) | Avg Turns: 3.9 vs 3.9 | Total Cost: $0.0656 vs $0.067

### Efficiency & Resource Usage Breakdown

| Metric | Config A (`config_baseline`) | Config B (`config_prompt_v2`) | Delta |
| :--- | :---: | :---: | :---: |
| **Avg Turns / Task** | 3.9 | 3.9 | +0.0 turns |
| **Avg Latency / Task** | 5.52s | 5.83s | +0.31s |
| **Total Tokens** | 46,388 | 47,099 | +711 |
| **Est. Total USD Cost** | $0.0656 | $0.0670 | $+0.0014 |

### Task-by-Task Outcome & Verdicts

| Task ID | Out A | Out B | Verdict A | Verdict B | Δ Score | Turns A/B | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `task_001` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_002` | FAIL | FAIL | PARTIAL | PARTIAL | 0.0 | 4 / 4 |  |
| `task_003` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_004` | PASS | PASS | FAILED | FAILED | 0.0 | 3 / 3 |  |
| `task_005` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_006` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_007` | FAIL | FAIL | PARTIAL | PARTIAL | 0.0 | 4 / 4 |  |
| `task_008` | FAIL | FAIL | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_009_adversarial` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 |  |
| `task_010` | FAIL | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | outcome changed |

---

## Comparison: config_baseline vs config_no_run_tests

**Summary**: [!] 1 regression(s): ['task_004'] | [OK] 2 improvement(s): ['task_008', 'task_010'] | Avg task-completion: 0.8 -> 1.0 (+0.2) | Avg Turns: 3.9 vs 4.0 | Total Cost: $0.0656 vs $0.0699

### Efficiency & Resource Usage Breakdown

| Metric | Config A (`config_baseline`) | Config B (`config_no_run_tests`) | Delta |
| :--- | :---: | :---: | :---: |
| **Avg Turns / Task** | 3.9 | 4.0 | +0.1 turns |
| **Avg Latency / Task** | 5.52s | 6.52s | +1.0s |
| **Total Tokens** | 46,388 | 45,422 | -966 |
| **Est. Total USD Cost** | $0.0656 | $0.0699 | $+0.0043 |

### Task-by-Task Outcome & Verdicts

| Task ID | Out A | Out B | Verdict A | Verdict B | Δ Score | Turns A/B | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `task_001` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_002` | FAIL | FAIL | PARTIAL | COMPLETE | 0.5 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_003` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_004` | PASS | FAIL | FAILED | COMPLETE | 1.0 | 3 / 4 | outcome changed; run_tests disappeared from flow (config_baseline->config_no_run_tests); edit_file: +1 calls; run_tests: -1 calls |
| `task_005` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_006` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_007` | FAIL | FAIL | PARTIAL | COMPLETE | 0.5 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_008` | FAIL | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | outcome changed; run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_009_adversarial` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_010` | FAIL | PASS | COMPLETE | COMPLETE | 0.0 | 4 / 4 | outcome changed; run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |

---
