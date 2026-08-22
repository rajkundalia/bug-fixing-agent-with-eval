"""
evals/outcome.py
----------------
Rule-based binary evaluator: did the tests pass?

This is the cheapest, fastest evaluator — the CI gate.
It reads directly from the agent's trace (last run_tests result)
rather than re-running pytest, so the eval is deterministic
with respect to the recorded run.
"""


import subprocess
import sys


def evaluate_outcome(result: dict, task: dict | None = None) -> dict:
    """Check whether the agent's last run_tests call returned passed=True,
    or run a post-hoc pytest check if run_tests was not called by the agent.

    Args:
        result: The dict returned by resolve_issue() — must contain 'trace'.
        task: Optional task dictionary containing test_file and test_filter.

    Returns:
        {
            "task_id":  str,
            "passed":   bool,   # True = tests passed = task succeeded
            "rationale": str,   # Brief human-readable explanation
        }
    """
    trace: list[dict] = result.get("trace", [])
    task_id: str = result.get("task_id", "unknown")

    # Walk the trace in reverse to find the last run_tests call
    last_test_result = None
    for entry in reversed(trace):
        if entry.get("tool") == "run_tests":
            last_test_result = entry.get("tool_result")
            break

    if last_test_result is not None:
        passed = bool(last_test_result.get("passed", False))
        output_snippet = (last_test_result.get("output") or "")[:300]
        return {
            "task_id": task_id,
            "passed": passed,
            "rationale": (
                "Tests passed on last run_tests call."
                if passed
                else f"Tests failed. Output snippet: {output_snippet!r}"
            ),
        }

    # Post-hoc evaluation when agent has no run_tests tool or never called it
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    if task and task.get("test_file"):
        cmd.append(task["test_file"])
    if task and task.get("test_filter"):
        cmd.extend(["-k", task["test_filter"]])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    passed = proc.returncode == 0
    output_snippet = (proc.stdout + proc.stderr)[:300]

    return {
        "task_id": task_id,
        "passed": passed,
        "rationale": (
            "Post-hoc tests passed."
            if passed
            else f"Post-hoc tests failed. Output snippet: {output_snippet!r}"
        ),
    }
