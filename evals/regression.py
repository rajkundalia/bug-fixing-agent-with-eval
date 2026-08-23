"""
evals/regression.py
--------------------
Rule-based regression runner: re-runs a set of previously-solved tasks
under the current config and flags any that have regressed (were passing
under a previous run, now fail).

Usage pattern:
  1. Run the full dataset → save results to a JSON file (via run_harness.py).
  2. After any prompt/model/tool change, run again → compare against saved.
  3. Call evaluate_regression(current_results, baseline_results) to surface
     which tasks went from PASS → FAIL (regressions) or FAIL → PASS (improvements).

Note: This module is a comparison utility library, not auto-invoked by the
harness. Callers must load two results JSON files and pass them in manually.
For automated cross-config comparison, see reports/compare_configs.py which
uses this module's logic internally.

CI Integration Note:
This script exits with code 1 when regressions are detected, making it drop-in
compatible with CI runners (e.g. GitHub Actions, GitLab CI). A pre-packaged
workflow is deliberately omitted as this repository is built for local evaluation.
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
        summary_parts.append(f"[!] {len(regressions)} regression(s): {regressions}")
    if improvements:
        summary_parts.append(f"[+] {len(improvements)} improvement(s): {improvements}")
    if not regressions and not improvements:
        summary_parts.append("No regressions. All previously-passing tasks still pass.")

    return {
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
        "summary": " | ".join(summary_parts),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: uv run python evals/regression.py <baseline_results.json> <current_results.json>")
        print("")
        print("Example:")
        print("  uv run python evals/regression.py \\")
        print("    reports/results_config_baseline_20260823_084331.json \\")
        print("    reports/results_config_baseline_20260824_120000.json")
        print("")
        print("Use this to detect regressions between two runs of the SAME config over time")
        print("(e.g. before and after a model update or prompt tweak).")
        print("For cross-config comparison, use: uv run python reports/compare_configs.py")
        sys.exit(1)

    baseline_path, current_path = sys.argv[1], sys.argv[2]
    baseline = load_results(baseline_path)
    current = load_results(current_path)

    report = evaluate_regression(current_results=current, baseline_results=baseline)

    print(f"\nBaseline : {baseline_path}")
    print(f"Current  : {current_path}")
    print(f"\nSummary  : {report['summary']}")

    if report["regressions"]:
        print(f"\n[!] Regressions ({len(report['regressions'])}):")
        for tid in report["regressions"]:
            print(f"   - {tid}  [was PASS -> now FAIL]")

    if report["improvements"]:
        print(f"\n[+] Improvements ({len(report['improvements'])}):")
        for tid in report["improvements"]:
            print(f"   - {tid}  [was FAIL -> now PASS]")

    print(f"\n   Unchanged: {len(report['unchanged'])} task(s)")
    sys.exit(1 if report["regressions"] else 0)

