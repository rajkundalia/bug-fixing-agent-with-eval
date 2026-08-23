"""
reports/compare_configs.py
---------------------------
Diffs evaluation results across two config runs.

Answers the two core comparison questions as separable experiments:
  - Baseline vs. config_prompt_v2   → isolates the prompt effect
  - Baseline vs. config_no_run_tests → isolates the tool effect

Target finding example:
  "Removing run_tests dropped task-completion scores from 0.81 avg to 0.34 avg,
   and tool_flow shows the agent now edits blindly without verifying."
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.tool_flow import compare_tool_flows


def load_results(path: str | Path) -> list[dict]:
    """Load a saved results file (list of per-task eval dicts)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare(
    results_a: list[dict],
    results_b: list[dict],
    label_a: str = "Config A",
    label_b: str = "Config B",
) -> dict:
    """Diff two sets of per-task eval results and surface key changes.

    Each result dict in the list must have at minimum:
      - task_id
      - outcome                   (bool)
      - task_completion_verdict   (str, optional)   — COMPLETE | PARTIAL | FAILED
      - task_completion_score     (float, optional) — derived from verdict
      - tool_flow                 (dict with 'flow' list, optional)

    Args:
        results_a:  Results from the first config (typically baseline).
        results_b:  Results from the second config.
        label_a:    Human-readable name for config A.
        label_b:    Human-readable name for config B.

    Returns:
        {
            "label_a":              str,
            "label_b":              str,
            "regressions":          list[str],   # tasks passing in A, failing in B
            "improvements":         list[str],   # tasks failing in A, passing in B
            "avg_completion_a":     float | None,
            "avg_completion_b":     float | None,
            "avg_completion_delta": float | None,
            "per_task":             list[dict],  # per-task breakdown
            "summary":              str,
        }
    """
    map_a = {res["task_id"]: res for res in results_a}
    map_b = {res["task_id"]: res for res in results_b}
    all_ids = sorted(set(map_a) | set(map_b))

    regressions = []
    improvements = []
    per_task = []

    scores_a, scores_b = [], []

    for task_id in all_ids:
        task_result_a = map_a.get(task_id, {})
        task_result_b = map_b.get(task_id, {})

        outcome_a = task_result_a.get("outcome", None)
        outcome_b = task_result_b.get("outcome", None)

        score_a = task_result_a.get("task_completion_score")
        score_b = task_result_b.get("task_completion_score")
        if score_a is not None:
            scores_a.append(score_a)
        if score_b is not None:
            scores_b.append(score_b)

        flow_a = task_result_a.get("tool_flow", {}).get("flow", [])
        flow_b = task_result_b.get("tool_flow", {}).get("flow", [])

        # Regression: was passing, now failing
        if outcome_a is True and outcome_b is False:
            regressions.append(task_id)
        elif outcome_a is False and outcome_b is True:
            improvements.append(task_id)

        flow_diff = compare_tool_flows(flow_a, flow_b, label_a, label_b)

        verdict_a = task_result_a.get("task_completion_verdict")
        verdict_b = task_result_b.get("task_completion_verdict")

        turns_a = task_result_a.get("turns_used", 0)
        turns_b = task_result_b.get("turns_used", 0)
        ms_a = task_result_a.get("total_ms", 0)
        ms_b = task_result_b.get("total_ms", 0)
        cost_a = task_result_a.get("cost_usd", 0.0)
        cost_b = task_result_b.get("cost_usd", 0.0)
        tokens_a = task_result_a.get("input_tokens", 0) + task_result_a.get("output_tokens", 0)
        tokens_b = task_result_b.get("input_tokens", 0) + task_result_b.get("output_tokens", 0)

        per_task.append({
            "task_id": task_id,
            "outcome_a": outcome_a,
            "outcome_b": outcome_b,
            "outcome_changed": outcome_a != outcome_b,
            "verdict_a": verdict_a,
            "verdict_b": verdict_b,
            "score_a": score_a,
            "score_b": score_b,
            "score_delta": round(score_b - score_a, 3) if (score_a is not None and score_b is not None) else None,
            "flow_diff": flow_diff,
            "flow_a": flow_a,
            "flow_b": flow_b,
            "turns_a": turns_a,
            "turns_b": turns_b,
            "ms_a": ms_a,
            "ms_b": ms_b,
            "cost_a": cost_a,
            "cost_b": cost_b,
            "tokens_a": tokens_a,
            "tokens_b": tokens_b,
        })

    avg_a = round(sum(scores_a) / len(scores_a), 3) if scores_a else None
    avg_b = round(sum(scores_b) / len(scores_b), 3) if scores_b else None
    delta = round(avg_b - avg_a, 3) if (avg_a is not None and avg_b is not None) else None

    # Efficiency summaries
    avg_turns_a = round(sum(pt["turns_a"] for pt in per_task) / len(per_task), 1) if per_task else 0
    avg_turns_b = round(sum(pt["turns_b"] for pt in per_task) / len(per_task), 1) if per_task else 0
    avg_sec_a = round(sum(pt["ms_a"] for pt in per_task) / (len(per_task) * 1000), 2) if per_task else 0
    avg_sec_b = round(sum(pt["ms_b"] for pt in per_task) / (len(per_task) * 1000), 2) if per_task else 0
    total_tokens_a = sum(pt["tokens_a"] for pt in per_task)
    total_tokens_b = sum(pt["tokens_b"] for pt in per_task)
    total_cost_a = round(sum(pt["cost_a"] for pt in per_task), 4)
    total_cost_b = round(sum(pt["cost_b"] for pt in per_task), 4)

    parts = []
    if regressions:
        parts.append(f"[!] {len(regressions)} regression(s): {regressions}")
    if improvements:
        parts.append(f"[OK] {len(improvements)} improvement(s): {improvements}")
    if delta is not None:
        direction = "+" if delta >= 0 else ""
        parts.append(f"Avg task-completion: {avg_a} -> {avg_b} ({direction}{delta})")
    parts.append(f"Avg Turns: {avg_turns_a} vs {avg_turns_b} | Total Cost: ${total_cost_a} vs ${total_cost_b}")
    if not parts:
        parts.append("No meaningful difference detected between configs.")

    return {
        "label_a": label_a,
        "label_b": label_b,
        "regressions": regressions,
        "improvements": improvements,
        "avg_completion_a": avg_a,
        "avg_completion_b": avg_b,
        "avg_completion_delta": delta,
        "efficiency_summary": {
            "avg_turns_a": avg_turns_a,
            "avg_turns_b": avg_turns_b,
            "avg_sec_a": avg_sec_a,
            "avg_sec_b": avg_sec_b,
            "total_tokens_a": total_tokens_a,
            "total_tokens_b": total_tokens_b,
            "total_cost_a": total_cost_a,
            "total_cost_b": total_cost_b,
        },
        "per_task": per_task,
        "summary": " | ".join(parts),
    }


def print_report(comparison: dict) -> None:
    """Pretty-print a comparison report to stdout."""
    print(f"\n{'='*70}")
    print(f"Config comparison: {comparison['label_a']}  vs.  {comparison['label_b']}")
    print(f"{'='*70}")
    print(f"Summary: {comparison['summary']}")
    print(f"\nPer-task breakdown:")
    print(f"{'Task ID':<25} {'Out A':>6} {'Out B':>6} {'Verdict A':>10} {'Verdict B':>10} {'dScore':>8}  Notes")
    print("-" * 90)
    for task_item in comparison["per_task"]:
        notes = []
        if task_item["outcome_changed"]:
            notes.append("outcome changed")
        flow_summary = task_item.get("flow_diff", {}).get("summary", "")
        if flow_summary and flow_summary != "Flows are identical in shape.":
            notes.append(flow_summary)
        verdict_a = task_item.get("verdict_a") or "—"
        verdict_b = task_item.get("verdict_b") or "—"
        print(
            f"{task_item['task_id']:<25} "
            f"{'PASS' if task_item['outcome_a'] else 'FAIL':>6} "
            f"{'PASS' if task_item['outcome_b'] else 'FAIL':>6} "
            f"{verdict_a:>10} "
            f"{verdict_b:>10} "
            f"{str(task_item['score_delta']) if task_item['score_delta'] is not None else 'N/A':>8}  "
            f"{', '.join(notes)}"
        )
    print()


def save_markdown_report(reports_list: list[dict], output_path: Path) -> None:
    """Write markdown comparison report to disk."""
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Benchmark Configuration Comparison Report",
        f"*Generated: {now_str} | Agent Model: `claude-haiku-4-5` | Judge Model: `claude-haiku-4-5`*\n"
    ]
    for report in reports_list:
        lines.append(f"## Comparison: {report['label_a']} vs {report['label_b']}\n")
        lines.append(f"**Summary**: {report['summary']}\n")

        eff = report.get("efficiency_summary", {})
        if eff:
            lines.append("### Efficiency & Resource Usage Breakdown\n")
            lines.append(f"| Metric | Config A (`{report['label_a']}`) | Config B (`{report['label_b']}`) | Delta |")
            lines.append("| :--- | :---: | :---: | :---: |")
            turns_delta = round(eff['avg_turns_b'] - eff['avg_turns_a'], 1)
            sec_delta = round(eff['avg_sec_b'] - eff['avg_sec_a'], 2)
            tok_delta = eff['total_tokens_b'] - eff['total_tokens_a']
            cost_delta = round(eff['total_cost_b'] - eff['total_cost_a'], 4)
            lines.append(f"| **Avg Turns / Task** | {eff['avg_turns_a']} | {eff['avg_turns_b']} | {turns_delta:+} turns |")
            lines.append(f"| **Avg Latency / Task** | {eff['avg_sec_a']}s | {eff['avg_sec_b']}s | {sec_delta:+}s |")
            lines.append(f"| **Total Tokens** | {eff['total_tokens_a']:,} | {eff['total_tokens_b']:,} | {tok_delta:+} |")
            lines.append(f"| **Est. Total USD Cost** | ${eff['total_cost_a']:.4f} | ${eff['total_cost_b']:.4f} | ${cost_delta:+.4f} |\n")

        lines.append("### Task-by-Task Outcome & Verdicts\n")
        lines.append("| Task ID | Out A | Out B | Verdict A | Verdict B | Δ Score | Turns A/B | Notes |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for task_item in report["per_task"]:
            notes = []
            if task_item["outcome_changed"]:
                notes.append("outcome changed")
            flow_summary = task_item.get("flow_diff", {}).get("summary", "")
            if flow_summary and flow_summary != "Flows are identical in shape.":
                notes.append(flow_summary)
            verdict_a = task_item.get("verdict_a") or "—"
            verdict_b = task_item.get("verdict_b") or "—"
            delta_str = str(task_item['score_delta']) if task_item['score_delta'] is not None else "N/A"
            out_a_str = "PASS" if task_item['outcome_a'] else "FAIL"
            out_b_str = "PASS" if task_item['outcome_b'] else "FAIL"
            turns_str = f"{task_item.get('turns_a', '—')} / {task_item.get('turns_b', '—')}"
            notes_str = "; ".join(notes)
            lines.append(f"| `{task_item['task_id']}` | {out_a_str} | {out_b_str} | {verdict_a} | {verdict_b} | {delta_str} | {turns_str} | {notes_str} |")
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved Markdown Report to: {output_path}")


if __name__ == "__main__":
    import sys
    reports_dir = Path("reports")
    all_reports = []

    if len(sys.argv) >= 3:
        path_a, path_b = sys.argv[1], sys.argv[2]
        label_a = sys.argv[3] if len(sys.argv) > 3 else Path(path_a).stem
        label_b = sys.argv[4] if len(sys.argv) > 4 else Path(path_b).stem

        results_a = load_results(path_a)
        results_b = load_results(path_b)
        report = compare(results_a, results_b, label_a, label_b)
        print_report(report)
        all_reports.append(report)
    else:
        # Find latest results for each known config
        configs = ["config_baseline", "config_prompt_v2", "config_no_run_tests"]
        latest_by_config = {}
        for cfg in configs:
            matching = sorted(reports_dir.glob(f"results_{cfg}_*.json"))
            if matching:
                latest_by_config[cfg] = matching[-1]

        if "config_baseline" in latest_by_config and "config_prompt_v2" in latest_by_config:
            path_a = latest_by_config["config_baseline"]
            path_b = latest_by_config["config_prompt_v2"]
            report = compare(load_results(path_a), load_results(path_b), "config_baseline", "config_prompt_v2")
            print_report(report)
            all_reports.append(report)

        if "config_baseline" in latest_by_config and "config_no_run_tests" in latest_by_config:
            path_a = latest_by_config["config_baseline"]
            path_b = latest_by_config["config_no_run_tests"]
            report = compare(load_results(path_a), load_results(path_b), "config_baseline", "config_no_run_tests")
            print_report(report)
            all_reports.append(report)

    if all_reports:
        save_markdown_report(all_reports, reports_dir / "comparison_report.md")
