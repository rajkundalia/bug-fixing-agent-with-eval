"""
evals/tool_flow.py
------------------
Rule-based evaluator: captures the shape/sequence of tool calls.

This is a trajectory-shape metric — not just which files got touched,
but the ORDER in which tools were called. Comparable across configs.

Key patterns flagged:
  - verification_missing:   run_tests never called (agent edited blind)
  - edit_before_read:       edit_file called before any read_file (blind edit)
  - loops:                  same tool called consecutively >2 times (stuck)
  - flow:                   the raw sequence e.g. ['read_file','edit_file','run_tests']
"""
from collections import Counter


def extract_tool_flow(trace: list[dict]) -> list[str]:
    """Return the ordered sequence of tool names called in the trace.

    Example: ['read_file', 'edit_file', 'run_tests', 'edit_file', 'run_tests']

    Args:
        trace: The 'trace' list from a resolve_issue() result.

    Returns:
        List of tool name strings (turns with no tool call are skipped).
    """
    tool_sequence = []
    for entry in trace:
        tool_name = entry.get("tool")
        if tool_name is not None:
            tool_sequence.append(tool_name)
    return tool_sequence


def evaluate_tool_flow(result: dict) -> dict:
    """Analyse the tool-call sequence for pathological patterns.

    Args:
        result: dict from resolve_issue() — must contain 'trace'.

    Returns:
        {
            "task_id":              str,
            "flow":                 list[str],  # raw sequence
            "verification_missing": bool,       # run_tests never called
            "edit_before_read":     bool,       # edit_file before any read_file
            "loops":                bool,       # same tool 3+ times in a row
            "tool_counts":          dict,       # {tool_name: count}
            "rationale":            str,
        }
    """
    trace: list[dict] = result.get("trace", [])
    task_id: str = result.get("task_id", "unknown")

    flow = extract_tool_flow(trace)
    tool_counts = dict(Counter(flow))

    verification_missing = "run_tests" not in flow

    # edit_before_read: edit_file appears in the flow before the first read_file
    edit_before_read = False
    has_read_any_file = False
    for tool in flow:
        if tool == "read_file":
            has_read_any_file = True
        if tool == "edit_file" and not has_read_any_file:
            edit_before_read = True
            break

    # loops: same tool name 3+ consecutive times
    loops = False
    streak = 1
    for i in range(1, len(flow)):
        if flow[i] == flow[i - 1]:
            streak += 1
            if streak >= 3:
                loops = True
                break
        else:
            streak = 1

    issues = []
    if verification_missing:
        issues.append("run_tests never called — agent edited without verifying")
    if edit_before_read:
        issues.append("edit_file called before reading the file — blind edit")
    if loops:
        issues.append("same tool called 3+ times consecutively — possible loop/stuck state")

    rationale = "; ".join(issues) if issues else "Tool flow looks healthy."

    return {
        "task_id": task_id,
        "flow": flow,
        "verification_missing": verification_missing,
        "edit_before_read": edit_before_read,
        "loops": loops,
        "tool_counts": tool_counts,
        "rationale": rationale,
    }


def compare_tool_flows(flow_a: list[str], flow_b: list[str], label_a: str = "A", label_b: str = "B") -> dict:
    """Compare two tool-call sequences and surface differences.

    Useful in compare_configs.py to flag what changed between runs.

    Args:
        flow_a: Tool sequence from config A.
        flow_b: Tool sequence from config B.
        label_a: Human-readable name for config A.
        label_b: Human-readable name for config B.

    Returns:
        {
            "length_delta":           int,    # len(B) - len(A)
            "verification_dropped":   bool,   # run_tests in A but not B
            "verification_added":     bool,   # run_tests in B but not A
            "edit_before_read_delta": str,    # change in that pattern
            "summary":                str,
        }
    """
    counts_a = Counter(flow_a)
    counts_b = Counter(flow_b)

    verification_dropped = ("run_tests" in flow_a) and ("run_tests" not in flow_b)
    verification_added = ("run_tests" not in flow_a) and ("run_tests" in flow_b)
    length_delta = len(flow_b) - len(flow_a)

    parts = []
    if verification_dropped:
        parts.append(f"run_tests disappeared from flow ({label_a}→{label_b})")
    if verification_added:
        parts.append(f"run_tests appeared in flow ({label_a}→{label_b})")
    if length_delta > 0:
        parts.append(f"flow got {length_delta} steps longer in {label_b}")
    elif length_delta < 0:
        parts.append(f"flow got {abs(length_delta)} steps shorter in {label_b}")

    for tool in set(list(counts_a.keys()) + list(counts_b.keys())):
        delta = counts_b.get(tool, 0) - counts_a.get(tool, 0)
        if delta != 0:
            parts.append(f"{tool}: {'+' if delta > 0 else ''}{delta} calls")

    return {
        "length_delta": length_delta,
        "verification_dropped": verification_dropped,
        "verification_added": verification_added,
        "summary": "; ".join(parts) if parts else "Flows are identical in shape.",
    }
