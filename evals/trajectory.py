"""
evals/trajectory.py
-------------------
Rule-based evaluator: inspects the shape of the agent's attempt trajectory.

Captures:
  - turns_used:         how many tool-call turns the agent took
  - dead_loop:          agent called the same tool repeatedly with the same args
  - never_edited:       agent read files but never made an edit
  - failed_after_max:   agent hit turn cap without passing tests
  - turns_to_pass:      turn index when tests first passed (None if never)
"""


def _args_key(args: dict | None) -> str:
    """Stable string key for a tool-call args dict (for loop detection)."""
    if not args:
        return ""
    return str(sorted(args.items()))


def evaluate_trajectory(result: dict) -> dict:
    """Analyse the agent's trajectory for loops, stalls, and efficiency.

    Args:
        result: dict from resolve_issue() — must contain 'trace' and 'turns_used'.

    Returns:
        {
            "task_id":          str,
            "turns_used":       int,
            "turns_to_pass":    int | None,  # turn index when tests first passed
            "dead_loop":        bool,        # same (tool, args) repeated ≥3 times
            "never_edited":     bool,        # no edit_file in the whole trace
            "failed_at_cap":    bool,        # hit max turns without passing
            "rationale":        str,
        }
    """
    trace: list[dict] = result.get("trace", [])
    task_id: str = result.get("task_id", "unknown")
    outcome: bool = result.get("outcome", False)
    turns_used: int = result.get("turns_used", len(trace))

    # turns_to_pass: index of first turn where run_tests returned passed=True
    turns_to_pass = None
    for i, entry in enumerate(trace):
        if entry.get("tool") == "run_tests":
            tr = entry.get("tool_result") or {}
            if tr.get("passed"):
                turns_to_pass = i
                break

    # dead_loop: same (tool, args) pair appearing ≥3 times
    call_counts: dict[str, int] = {}
    dead_loop = False
    for entry in trace:
        tool = entry.get("tool")
        if tool is None:
            continue
        key = f"{tool}::{_args_key(entry.get('args'))}"
        call_counts[key] = call_counts.get(key, 0) + 1
        if call_counts[key] >= 3:
            dead_loop = True
            break

    has_edited = False
    for entry in trace:
        if entry.get("tool") == "edit_file":
            has_edited = True
            break
    never_edited = not has_edited
    failed_at_cap = not outcome and turns_used > 0

    issues = []
    if dead_loop:
        issues.append("dead loop detected — same call repeated ≥3 times")
    if never_edited:
        issues.append("agent never called edit_file — no fix attempted")
    if failed_at_cap:
        issues.append(f"task failed after {turns_used} turns")
    if turns_to_pass is not None:
        issues.append(f"tests passed at turn {turns_to_pass}")

    return {
        "task_id": task_id,
        "turns_used": turns_used,
        "turns_to_pass": turns_to_pass,
        "dead_loop": dead_loop,
        "never_edited": never_edited,
        "failed_at_cap": failed_at_cap,
        "rationale": "; ".join(issues) if issues else "Trajectory looks clean.",
    }
