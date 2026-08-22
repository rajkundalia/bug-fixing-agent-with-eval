"""
run_harness.py
--------------
Main entry point: runs the full task dataset under one or more configs
and saves per-task eval results to reports/.

Usage:
    uv run python run_harness.py                          # all tasks, baseline config
    uv run python run_harness.py --config config_baseline --config config_no_run_tests
    uv run python run_harness.py --task task_001_empty_list  # single task smoke test

Results are saved to reports/results_<config_id>_<timestamp>.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

from agents.issue_resolver import resolve_issue
from evals.outcome import evaluate_outcome
from evals.tool_correctness import evaluate_tool_correctness
from evals.tool_flow import evaluate_tool_flow
from evals.trajectory import evaluate_trajectory
from evals.efficiency import evaluate_efficiency
from evals.adversarial import evaluate_adversarial
from evals.safety import evaluate_safety, _parse_failing_tests
from evals.task_completion import evaluate_task_completion
from evals.fix_quality import evaluate_fix_quality


def load_config(config_id: str) -> dict:
    path = Path("configs") / f"{config_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_tasks(task_filter: str | None = None) -> list[dict]:
    tasks = []
    for task_file_path in sorted(Path("datasets").glob("task_*.json")):
        task = json.loads(task_file_path.read_text(encoding="utf-8"))
        if task_filter and task["id"] != task_filter:
            continue
        tasks.append(task)
    return tasks


def _capture_baseline_failures() -> set[str]:
    """Run the full test suite and return the set of currently-failing test IDs.

    Called BEFORE the agent runs so evaluate_safety() can distinguish
    pre-existing failures (from the planted bug) from agent-introduced ones.
    """
    import subprocess
    proc = subprocess.run(
        ["uv", "run", "pytest", "-v", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return _parse_failing_tests(proc.stdout + proc.stderr)


def run_one(task: dict, config: dict, use_llm_judge: bool) -> dict:
    """Run a single task under a config and evaluate all metrics."""
    print(f"  → Running {task['id']} ... ", end="", flush=True)

    # Capture which tests are already failing BEFORE the agent touches anything
    baseline_failures = _capture_baseline_failures()

    result = resolve_issue(task=task, config=config)
    print(f"{'PASS' if result['outcome'] else 'FAIL'} ({result['turns_used']} turns, {result['total_ms']}ms)")

    # Rule-based evals (always run)
    outcome = evaluate_outcome(result)
    tool_correctness = evaluate_tool_correctness(result, task)
    tool_flow = evaluate_tool_flow(result)
    trajectory = evaluate_trajectory(result)
    efficiency = evaluate_efficiency(result)
    safety = evaluate_safety(result, task, baseline_failures=baseline_failures)

    row = {
        "task_id": task["id"],
        "config_id": config["id"],
        "outcome": outcome["passed"],
        "tool_correctness_score": tool_correctness["score"],
        "tool_flow": tool_flow,
        "trajectory": trajectory,
        "efficiency": efficiency,
        "safe": safety["safe"],
        "safety_new_failures": safety["new_failures"],
        "trace": result["trace"],
        "turns_used": result["turns_used"],
        "total_ms": result["total_ms"],
    }

    # Adversarial eval (only for adversarial tasks)
    if task.get("adversarial_content"):
        row["adversarial"] = evaluate_adversarial(result, task)

    # LLM-judge evals (optional — slow, costs model time)
    if use_llm_judge:
        task_completion_result = evaluate_task_completion(result, task)
        fix_quality_result = evaluate_fix_quality(result, task)
        row["task_completion_verdict"] = task_completion_result.get("verdict")
        row["task_completion_score"] = task_completion_result.get("score")
        row["task_completion_rationale"] = task_completion_result.get("rationale")
        row["fix_quality_verdict"] = fix_quality_result.get("verdict")
        row["fix_quality_score"] = fix_quality_result.get("score")
        row["fix_quality_is_workaround"] = fix_quality_result.get("is_workaround")
        row["fix_quality_rationale"] = fix_quality_result.get("rationale")

    return row


def main():
    parser = argparse.ArgumentParser(description="Bug-fixing agent eval harness")
    parser.add_argument(
        "--config", action="append", dest="configs",
        default=["config_baseline"],
        help="Config ID(s) to run (can be specified multiple times)",
    )
    parser.add_argument("--task", default=None, help="Run only this task ID")
    parser.add_argument(
        "--judge", action="store_true", default=False,
        help="Also run LLM-judge evaluators (task_completion, fix_quality) — slow",
    )
    args = parser.parse_args()

    Path("reports").mkdir(exist_ok=True)

    for config_id in args.configs:
        config = load_config(config_id)
        tasks = load_tasks(args.task)

        if not tasks:
            print(f"No tasks found (filter: {args.task})")
            sys.exit(1)

        print(f"\nConfig: {config_id}  |  Tasks: {len(tasks)}  |  Judge: {args.judge}")
        print("=" * 60)

        all_results = []
        for task in tasks:
            row = run_one(task, config, use_llm_judge=args.judge)
            all_results.append(row)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_path = Path("reports") / f"results_{config_id}_{timestamp}.json"

        # Save full results (excluding trace to keep it readable; trace saved separately)
        summary_rows = [{key: value for key, value in result_row.items() if key != "trace"} for result_row in all_results]
        out_path.write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")

        # Save traces separately
        trace_path = Path("reports") / f"traces_{config_id}_{timestamp}.json"
        trace_rows = [{"task_id": result_row["task_id"], "trace": result_row["trace"]} for result_row in all_results]
        trace_path.write_text(json.dumps(trace_rows, indent=2), encoding="utf-8")

        passed = sum(1 for result_row in all_results if result_row["outcome"])
        print(f"\nResults: {passed}/{len(all_results)} passed")
        print(f"Saved:   {out_path}")
        print(f"Traces:  {trace_path}")


if __name__ == "__main__":
    main()
