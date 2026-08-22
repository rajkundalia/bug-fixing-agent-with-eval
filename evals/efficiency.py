"""
evals/efficiency.py
-------------------
Rule-based evaluator: cost, latency, and tool-call count per run.

These are "functional" metrics — the agent can be correct but expensive.
Tracked on the regression suite so a prompt/model swap that multiplies
token usage 5× is flagged even if accuracy stays the same.
"""


def evaluate_efficiency(result: dict) -> dict:
    """Compute efficiency metrics from the agent's run result.

    Args:
        result: dict from resolve_issue() — must contain 'trace' and 'total_ms'.

    Returns:
        {
            "task_id":          str,
            "total_ms":         int,    # wall-clock time for the whole run
            "tool_call_count":  int,    # total tool calls made
            "edit_count":       int,    # number of edit_file calls
            "read_count":       int,    # number of read_file calls
            "test_run_count":   int,    # number of run_tests calls
            "no_tool_turns":    int,    # turns with no tool call (wasted turns)
            "rationale":        str,
        }
    """
    trace: list[dict] = result.get("trace", [])
    task_id: str = result.get("task_id", "unknown")
    total_ms: int = result.get("total_ms", 0)

    tool_calls = [e for e in trace if e.get("tool") is not None]
    no_tool_turns = len(trace) - len(tool_calls)

    counts = {"read_file": 0, "edit_file": 0, "run_tests": 0}
    for entry in tool_calls:
        tool = entry.get("tool", "")
        if tool in counts:
            counts[tool] += 1

    notes = []
    if no_tool_turns > 0:
        notes.append(f"{no_tool_turns} turn(s) with no tool call (wasted)")
    if counts["run_tests"] == 0:
        notes.append("run_tests never called — verification skipped")
    if counts["edit_file"] > 4:
        notes.append(f"high edit count ({counts['edit_file']}) — may indicate flailing")

    return {
        "task_id": task_id,
        "total_ms": total_ms,
        "tool_call_count": len(tool_calls),
        "edit_count": counts["edit_file"],
        "read_count": counts["read_file"],
        "test_run_count": counts["run_tests"],
        "no_tool_turns": no_tool_turns,
        "rationale": "; ".join(notes) if notes else "Efficiency looks normal.",
    }
