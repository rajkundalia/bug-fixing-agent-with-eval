"""
run_judge.py
------------
Decoupled post-processing LLM Judge evaluator.

Reads saved traces (`reports/traces_*.json`) and results (`reports/results_*.json`),
runs the LLM-as-a-judge (`llama3.2:3b`) on each task trace, and updates the results file
with task_completion and fix_quality verdicts.

Usage:
    uv run python run_judge.py --config config_baseline
    uv run python run_judge.py reports/results_config_baseline_20260822_230856.json
"""

import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from evals.task_completion import evaluate_task_completion
from evals.fix_quality import evaluate_fix_quality
from run_harness import load_tasks


def judge_file(results_file: Path, traces_file: Path, tasks_by_id: dict):
    print(f"\nJudging: {results_file.name}")
    print("=" * 60)

    results = json.loads(results_file.read_text(encoding="utf-8"))
    traces = json.loads(traces_file.read_text(encoding="utf-8"))

    trace_map = {trace_entry["task_id"]: trace_entry["trace"] for trace_entry in traces}

    updated_results = []
    for row in results:
        task_id = row["task_id"]
        task = tasks_by_id.get(task_id)
        if not task:
            print(f"Skipping unknown task {task_id}")
            updated_results.append(row)
            continue

        trace = trace_map.get(task_id, [])
        result_struct = {
            "task": task,
            "outcome": {"passed": row.get("outcome", False)},
            "trace": trace,
            "edited_files": [],
        }

        print(f"  -> Judging {task_id} ... ", end="", flush=True)

        task_comp = evaluate_task_completion(result_struct, task)
        fix_qual = evaluate_fix_quality(result_struct, task)

        row["task_completion_verdict"] = task_comp.get("verdict")
        row["task_completion_score"] = task_comp.get("score")
        row["task_completion_rationale"] = task_comp.get("rationale")
        row["fix_quality_verdict"] = fix_qual.get("verdict")
        row["fix_quality_score"] = fix_qual.get("score")
        row["fix_quality_is_workaround"] = fix_qual.get("is_workaround")
        row["fix_quality_rationale"] = fix_qual.get("rationale")

        print(f"Verdict: {task_comp.get('verdict')} / {fix_qual.get('verdict')}")
        updated_results.append(row)

    results_file.write_text(json.dumps(updated_results, indent=2), encoding="utf-8")
    print(f"Updated results saved to {results_file}")


def main():
    parser = argparse.ArgumentParser(description="Standalone LLM-Judge evaluator")
    parser.add_argument("file", nargs="?", default=None, help="Path to specific results_*.json file")
    parser.add_argument("--config", default=None, help="Config ID to judge (finds latest results file)")
    parser.add_argument("--all", action="store_true", help="Judge the latest results file for ALL configs")

    args = parser.parse_args()

    all_tasks = load_tasks()
    tasks_by_id = {task["id"]: task for task in all_tasks}

    reports_dir = Path("reports")

    if args.all:
        all_res_files = sorted(reports_dir.glob("results_*.json"))
        # Group by config_id to find latest file per config
        latest_by_config = {}
        for rf in all_res_files:
            # Filename pattern: results_{config_id}_{timestamp}.json
            parts = rf.stem.split("_")
            if len(parts) >= 3:
                config_id = "_".join(parts[1:-2]) if len(parts) > 3 else parts[1]
                latest_by_config[config_id] = rf

        for config_id, latest_res in latest_by_config.items():
            latest_tr = reports_dir / latest_res.name.replace("results_", "traces_")
            if latest_tr.exists():
                print(f"\n--- Judging Config: {config_id} ---")
                judge_file(latest_res, latest_tr, tasks_by_id)

    elif args.file:
        res_path = Path(args.file)
        tr_path = reports_dir / res_path.name.replace("results_", "traces_")
        if not res_path.exists() or not tr_path.exists():
            print(f"Error: {res_path} or {tr_path} not found")
            sys.exit(1)
        judge_file(res_path, tr_path, tasks_by_id)

    elif args.config:
        matching_res = sorted(reports_dir.glob(f"results_{args.config}_*.json"))
        if not matching_res:
            print(f"No results found for config '{args.config}'")
            sys.exit(1)
        latest_res = matching_res[-1]
        latest_tr = reports_dir / latest_res.name.replace("results_", "traces_")
        judge_file(latest_res, latest_tr, tasks_by_id)

    else:
        # Default to latest result file in reports/
        matching_res = sorted(reports_dir.glob("results_*.json"))
        if not matching_res:
            print("No results JSON files found in reports/")
            sys.exit(1)
        latest_res = matching_res[-1]
        latest_tr = reports_dir / latest_res.name.replace("results_", "traces_")
        judge_file(latest_res, latest_tr, tasks_by_id)


if __name__ == "__main__":
    main()
