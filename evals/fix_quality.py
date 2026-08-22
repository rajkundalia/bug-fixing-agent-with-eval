"""
evals/fix_quality.py
---------------------
LLM-judge evaluator: genuine root-cause fix vs. workaround?

Catches the "workaround trap": a test can pass even when the agent:
  - deleted or weakened an assertion
  - added a broad try/except to swallow the error
  - hardcoded a return value that passes only the specific test
  - edited the test file instead of the source

The judge compares the agent's diff against the task's planted_root_cause
to assess whether the fix is genuine.
"""

from judges.llm_judge import judge_fix_quality


def evaluate_fix_quality(result: dict, task: dict, agent_diff: str = "") -> dict:
    """Evaluate fix quality using the LLM judge.

    Args:
        result:     dict from resolve_issue() — must contain 'trace'.
        task:       Task definition dict — must contain 'description'
                    and 'planted_root_cause'.
        agent_diff: The diff or new file content after the agent's edits.
                    Pass this for best judge accuracy; if omitted the judge
                    falls back to reading the trace alone.

    Returns:
        {
            "task_id":       str,
            "verdict":       str,   # GENUINE | PARTIAL | WORKAROUND | FAILED
            "score":         float, # derived from verdict: 1.0 / 0.5 / 0.0
            "is_workaround": bool,
            "rationale":     str,
        }
    """
    task_id: str = result.get("task_id", "unknown")
    judgment = judge_fix_quality(task=task, result=result, agent_diff=agent_diff)

    return {
        "task_id": task_id,
        **judgment,  # verdict, score, is_workaround, rationale (or error)
    }
