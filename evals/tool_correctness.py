"""
evals/tool_correctness.py
--------------------------
Rule-based evaluator: did the agent open and modify the right files?

Compares the set of files the agent read and edited against the
expected files recorded in the task definition.
"""


def evaluate_tool_correctness(result: dict, task: dict) -> dict:
    """Check whether the agent interacted with the correct files.

    Args:
        result: dict from resolve_issue() — must contain 'trace'.
        task:   Task definition dict — uses 'target_file' and 'test_file'.

    Returns:
        {
            "task_id":          str,
            "read_correct":     bool,   # target_file was read at least once
            "edited_correct":   bool,   # target_file was edited at least once
            "edited_test_file": bool,   # test_file was edited (bad — workaround)
            "files_read":       list,
            "files_edited":     list,
            "score":            float,  # 0.0 / 0.5 / 1.0
            "rationale":        str,
        }
    """
    trace: list[dict] = result.get("trace", [])
    task_id: str = result.get("task_id", "unknown")
    target_file: str = task.get("target_file", "")
    test_file: str = task.get("test_file", "")

    files_read = []
    for entry in trace:
        if entry.get("tool") == "read_file" and entry.get("args"):
            file_path = entry["args"].get("path")
            if file_path:
                files_read.append(file_path)

    files_edited = []
    for entry in trace:
        if entry.get("tool") == "edit_file" and entry.get("args"):
            file_path = entry["args"].get("path")
            if file_path:
                files_edited.append(file_path)

    read_correct = target_file in files_read
    edited_correct = target_file in files_edited
    edited_test = test_file in files_edited if test_file else False

    # Scoring rubric:
    # 1.0  = read AND edited the correct file, did NOT edit the test file
    # 0.5  = edited the correct file but also edited the test file (partial workaround)
    # 0.25 = read the file but didn't edit it
    # 0.0  = didn't interact with the correct file at all, or only edited test
    if edited_correct and not edited_test:
        score = 1.0
        rationale = "Agent correctly read and edited only the target source file."
    elif edited_correct and edited_test:
        score = 0.5
        rationale = (
            f"Agent edited the target file but ALSO edited the test file ({test_file!r})."
            " Partial workaround detected."
        )
    elif read_correct and not edited_correct:
        score = 0.25
        rationale = "Agent read the target file but did not edit it — no fix attempted."
    else:
        score = 0.0
        rationale = (
            f"Agent did not interact with the expected target file ({target_file!r})."
        )

    return {
        "task_id": task_id,
        "read_correct": read_correct,
        "edited_correct": edited_correct,
        "edited_test_file": edited_test,
        "files_read": files_read,
        "files_edited": files_edited,
        "score": score,
        "rationale": rationale,
    }
