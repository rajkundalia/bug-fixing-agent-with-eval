"""
evals/regression.py
--------------------
Rule-based regression runner: re-runs a set of previously-solved tasks
under the current config and flags any that have regressed (were passing
under a previous run, now fail).

Usage pattern:
  1. Run the full dataset → save results to a JSON file.
  2. After any prompt/model/tool change, run again → compare against saved.
  3. Any task that was passing before and fails now is a regression.

This file provides the comparison logic. The actual re-running is done
by the main run_harness.py script.
"""
import json
from pathlib import Path


def load_results(path: str | Path) -> list[dict]:
    """Load a saved results file (list of per-task result dicts)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_regression(
    current_results: list[dict],
    baseline_results: list[dict],
) -> dict:
    """Compare current results against a baseline to find regressions.

    Args:
        current_results:  List of result dicts from the current run.
        baseline_results: List of result dicts from the baseline (golden) run.

    Returns:
        {
            "regressions":  list[str],  # task IDs that regressed
            "improvements": list[str],  # task IDs that newly pass
            "unchanged":    list[str],  # task IDs with same outcome
            "summary":      str,
        }
    """
    baseline_map = {r["task_id"]: r for r in baseline_results}
    current_map = {r["task_id"]: r for r in current_results}

    regressions = []
    improvements = []
    unchanged = []

    all_ids = set(baseline_map) | set(current_map)
    for task_id in sorted(all_ids):
        base = baseline_map.get(task_id)
        curr = current_map.get(task_id)

        base_pass = base.get("outcome", False) if base else None
        curr_pass = curr.get("outcome", False) if curr else None

        if base_pass is True and curr_pass is False:
            regressions.append(task_id)
        elif base_pass is False and curr_pass is True:
            improvements.append(task_id)
        else:
            unchanged.append(task_id)

    summary_parts = []
    if regressions:
        summary_parts.append(f"⚠ {len(regressions)} regression(s): {regressions}")
    if improvements:
        summary_parts.append(f"✓ {len(improvements)} improvement(s): {improvements}")
    if not regressions and not improvements:
        summary_parts.append("No regressions. All previously-passing tasks still pass.")

    return {
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
        "summary": " | ".join(summary_parts),
    }
