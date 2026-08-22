"""
agents/issue_resolver.py
------------------------
The agent loop: runs qwen3:8b via Ollama with native tool-calling.

Every turn is captured in a structured trace list — this trace IS the
primary input for all evaluators (tool_correctness, trajectory, fix_quality,
adversarial, efficiency, etc.).

Trace entry shape per turn:
{
    "turn": int,
    "tool": str | None,          # name of tool called, or None for final text
    "args": dict | None,         # args passed to the tool
    "tool_result": any | None,   # what the tool returned
    "model_content": str,        # model's text response / reasoning
    "timestamp_ms": int,         # wall-clock ms at turn start (for latency)
}

Usage:
    from agents.issue_resolver import resolve_issue
    result = resolve_issue(task, config)
"""

import time
import json
from pathlib import Path
from ollama import chat

from agents.tools import TOOL_REGISTRY, read_file, edit_file, run_tests


def resolve_issue(task: dict, config: dict) -> dict:
    """Run the agent loop for one task under a given config.

    Args:
        task: Task dict loaded from datasets/task_*.json.
              Required keys: id, description, target_file, test_file, max_turns.
        config: Config dict loaded from configs/config_*.json.
                Required keys: prompt_version, system_prompt, tools.

    Returns:
        {
            "task_id":    str,
            "config_id":  str,
            "trace":      list[dict],   # full turn-by-turn log
            "turns_used": int,
            "outcome":    bool,         # True if final run_tests passed
            "total_ms":   int,          # wall-clock time for entire run
        }
    """
    max_turns: int = task.get("max_turns", 5)
    model: str = config.get("model", "qwen3:8b")
    system_prompt: str = config["system_prompt"]
    enabled_tools: list[str] = config.get("tools", ["read_file", "edit_file", "run_tests"])

    # Build the tool objects to pass to ollama (only enabled ones)
    tool_fns = [TOOL_REGISTRY[tool_name] for tool_name in enabled_tools if tool_name in TOOL_REGISTRY]

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"{task['description']}\nTarget file: {task['target_file']}",
        },
    ]

    trace: list[dict] = []
    outcome = False
    run_start = time.time()

    for turn in range(max_turns):
        turn_start_ms = int(time.time() * 1000)

        response = chat(
            model=model,
            messages=messages,
            tools=tool_fns if tool_fns else None,
        )

        message = response.message

        if message.tool_calls:
            # Append the assistant's tool-call message to history
            messages.append(message)

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments or {}
                print(f"\n    [Turn {turn+1}] Tool Call -> {function_name}({function_args})", flush=True)

                # Dispatch to the real function
                if function_name in TOOL_REGISTRY and function_name in enabled_tools:
                    tool_result = TOOL_REGISTRY[function_name](**function_args)
                else:
                    tool_result = {"error": f"Tool '{function_name}' not available in this config."}

                # Log the turn
                entry = {
                    "turn": turn,
                    "tool": function_name,
                    "args": function_args,
                    "tool_result": tool_result,
                    "model_content": message.content or "",
                    "timestamp_ms": turn_start_ms,
                }
                trace.append(entry)

                # Feed tool result back as a tool message
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                })

                # Check if we just ran tests and they passed — we can stop
                if function_name == "run_tests" and isinstance(tool_result, dict):
                    if tool_result.get("passed"):
                        outcome = True
                        break

            if outcome:
                break

        else:
            # Model responded with plain text — either done or stuck
            snippet = (message.content or "").strip().replace('\n', ' ')
            print(f"\n    [Turn {turn+1}] Text Response -> {snippet[:80]}...", flush=True)
            entry = {
                "turn": turn,
                "tool": None,
                "args": None,
                "tool_result": None,
                "model_content": message.content or "",
                "timestamp_ms": turn_start_ms,
            }
            trace.append(entry)
            messages.append(message)
            break

    total_ms = int((time.time() - run_start) * 1000)

    return {
        "task_id": task["id"],
        "config_id": config["id"],
        "trace": trace,
        "turns_used": len(trace),
        "outcome": outcome,
        "total_ms": total_ms,
    }
