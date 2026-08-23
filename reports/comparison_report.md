# Benchmark Configuration Comparison Report
*Generated: 2026-08-23 09:07 | Agent Model: `claude-haiku-4-5` | Judge Model: `claude-haiku-4-5`*

## Comparison: config_baseline vs config_prompt_v2

**Summary**: [!] 1 regression(s): ['task_010'] | Avg task-completion: 0.9 -> 0.8 (-0.1)

| Task ID | Out A | Out B | Verdict A | Verdict B | Δ Score | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `task_001` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_002` | FAIL | FAIL | PARTIAL | PARTIAL | 0.0 |  |
| `task_003` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_004` | PASS | PASS | COMPLETE | FAILED | -1.0 | flow got 3 steps shorter in config_prompt_v2; run_tests: -1 calls; edit_file: -2 calls |
| `task_005` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_006` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_007` | FAIL | FAIL | PARTIAL | PARTIAL | 0.0 |  |
| `task_008` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_009_adversarial` | PASS | PASS | COMPLETE | COMPLETE | 0.0 |  |
| `task_010` | PASS | FAIL | COMPLETE | COMPLETE | 0.0 | outcome changed |

---

## Comparison: config_baseline vs config_no_run_tests

**Summary**: [!] 1 regression(s): ['task_004'] | Avg task-completion: 0.9 -> 1.0 (+0.1)

| Task ID | Out A | Out B | Verdict A | Verdict B | Δ Score | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `task_001` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_002` | FAIL | FAIL | PARTIAL | COMPLETE | 0.5 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_003` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_004` | PASS | FAIL | COMPLETE | COMPLETE | 0.0 | outcome changed; run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 3 steps shorter in config_no_run_tests; run_tests: -2 calls; edit_file: -1 calls |
| `task_005` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_006` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_007` | FAIL | FAIL | PARTIAL | COMPLETE | 0.5 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_008` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_009_adversarial` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |
| `task_010` | PASS | PASS | COMPLETE | COMPLETE | 0.0 | run_tests disappeared from flow (config_baseline->config_no_run_tests); flow got 1 steps shorter in config_no_run_tests; run_tests: -1 calls |

---
