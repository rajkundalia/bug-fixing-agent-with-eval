"""
evals/outcome.py
----------------
Rule-based binary evaluator: did the tests pass?

This is the cheapest, fastest evaluator — the CI gate.
It reads directly from the agent's trace (last run_tests result)
rather than re-running pytest, so the eval is deterministic
with respect to the recorded run.
"""


def evaluate_outcome(result: dict) -> dict:
    """Check whether the agent's last run_tests call returned passed=True.

    Args:
        result: The dict returned by resolve_issue() — must contain 'trace'.

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

    if last_test_result is None:
        return {
            "task_id": task_id,
            "passed": False,
            "rationale": "Agent never called run_tests — could not verify outcome.",
        }

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
