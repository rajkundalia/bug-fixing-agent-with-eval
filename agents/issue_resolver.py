"""
agents/issue_resolver.py
------------------------
The agent loop: runs Claude via Anthropic API with native tool-calling.

Every turn is captured in a structured trace list — this trace IS the
primary input for all evaluators (tool_correctness, trajectory, fix_quality,
adversarial, efficiency, etc.).
"""

import os
import time
import json
from pathlib import Path
import anthropic

from agents.tools import TOOL_REGISTRY, read_file, edit_file, run_tests


ANTHROPIC_TOOL_DEFINITIONS = {
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a source file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to file"}
            },
            "required": ["path"]
        }
    },
    "edit_file": {
        "name": "edit_file",
        "description": "Overwrite a file with complete new content. IMPORTANT: This tool overwrites the entire file on disk. You MUST provide the ENTIRE file content, including all existing functions and imports.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to file"},
                "content": {"type": "string", "description": "Full content of the file"}
            },
            "required": ["path", "content"]
        }
    },
    "run_tests": {
        "name": "run_tests",
        "description": "Run the pytest test suite for a specific test file or filter pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Optional relative path to test file (e.g. 'tests/test_calculator.py')"},
                "filter": {"type": "string", "description": "Optional -k filter pattern (e.g. 'calculate_total')"}
            }
        }
    }
}


def resolve_issue(task: dict, config: dict) -> dict:
    """Run the agent loop for one task under a given config."""
    client = anthropic.Anthropic()
    max_turns: int = task.get("max_turns", 5)
    model: str = config.get("model", "claude-haiku-4-5")
    system_prompt: str = config["system_prompt"]
    enabled_tools: list[str] = config.get("tools", ["read_file", "edit_file", "run_tests"])

    tools = [ANTHROPIC_TOOL_DEFINITIONS[tool_name] for tool_name in enabled_tools if tool_name in ANTHROPIC_TOOL_DEFINITIONS]

    user_content = (
        f"{task['description']}\n"
        f"Target file: {task['target_file']}\n"
        f"Test file: {task.get('test_file', '')}"
    )
    if task.get("test_filter"):
        user_content += f"\nTest filter: {task['test_filter']}"

    messages = [
        {
            "role": "user",
            "content": user_content,
        }
    ]

    trace: list[dict] = []
    outcome = False
    run_start = time.time()

    for turn in range(max_turns):
        turn_start_ms = int(time.time() * 1000)

        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            tools=tools if tools else anthropic.NOT_GIVEN,
        )

        # Extract all tool_use blocks from the response.
        # Note: Anthropic Messages API supports parallel tool calling (multiple tool_use blocks in a single turn).
        tool_blocks = [block for block in response.content if block.type == "tool_use"]

        if tool_blocks:
            messages.append({"role": "assistant", "content": response.content})
            tool_results_content = []

            is_parallel = len(tool_blocks) > 1
            for call_idx, block in enumerate(tool_blocks, start=1):
                function_name = block.name
                function_args = block.input or {}
                tool_use_id = block.id

                turn_label = f"[Turn {turn+1}.{call_idx}] (Parallel)" if is_parallel else f"[Turn {turn+1}]"
                print(f"\n    {turn_label} Tool Call -> {function_name}({function_args})", flush=True)

                if function_name in TOOL_REGISTRY and function_name in enabled_tools:
                    try:
                        tool_result = TOOL_REGISTRY[function_name](**function_args)
                    except Exception as err:
                        tool_result = {"error": f"Failed to execute '{function_name}': {err}"}
                else:
                    tool_result = {"error": f"Tool '{function_name}' not available."}

                entry = {
                    "turn": turn,
                    "tool": function_name,
                    "args": function_args,
                    "tool_result": tool_result,
                    "model_content": "",
                    "timestamp_ms": turn_start_ms,
                }
                trace.append(entry)

                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(tool_result),
                })

                if function_name == "run_tests" and isinstance(tool_result, dict):
                    if tool_result.get("passed"):
                        outcome = True

            messages.append({"role": "user", "content": tool_results_content})
            if outcome:
                break
        else:
            text_blocks = [block.text for block in response.content if block.type == "text"]
            text_content = "\n".join(text_blocks)
            snippet = text_content.strip().replace('\n', ' ')
            print(f"\n    [Turn {turn+1}] Text Response -> {snippet[:80]}...", flush=True)

            entry = {
                "turn": turn,
                "tool": None,
                "args": None,
                "tool_result": None,
                "model_content": text_content,
                "timestamp_ms": turn_start_ms,
            }
            trace.append(entry)
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


