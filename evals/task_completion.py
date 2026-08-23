"""
evals/task_completion.py
-------------------------
LLM-judge evaluator: how effectively did the agent accomplish the goal?

The judge returns a verdict (COMPLETE / PARTIAL / FAILED) with a rationale.
A numeric score is derived deterministically from the verdict — richer signal
than the binary outcome.py gate, without asking the LLM to invent a number.

Run both side by side:
  - outcome.py         → cheap binary CI gate  (tests pass?)
  - task_completion.py → verdict + score + rationale (how well did it do?)

The judge uses claude-haiku-4-5 to evaluate task completion trajectories.
"""

from judges.llm_judge import judge_task_completion


def evaluate_task_completion(result: dict, task: dict) -> dict:
    """Evaluate task completion using the LLM judge.

    Args:
        result: dict from resolve_issue() — must contain 'trace'.
        task:   Task definition dict — must contain 'description'.

    Returns:
        {
            "task_id":  str,
            "verdict":  str,    # COMPLETE | PARTIAL | FAILED  (from judge)
            "score":    float,  # derived from verdict: 1.0 / 0.5 / 0.0
            "rationale": str,
        }
    """
    task_id: str = result.get("task_id", "unknown")
    judgment = judge_task_completion(task=task, result=result)

    return {
        "task_id": task_id,
        **judgment,  # verdict, score, rationale (or error)
    }
