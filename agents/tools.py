"""
agents/tools.py
---------------
The three tools available to the bug-fixing agent.
These are passed directly to the Ollama `chat()` call via `tools=[...]`,
so their docstrings and type annotations ARE the tool schema the model sees.

Design note: keep these thin wrappers — all side-effect logic lives here
so the agent loop (issue_resolver.py) stays clean and testable.
"""

import sys
import subprocess
from pathlib import Path


def read_file(path: str) -> str:
    """Read and return the full contents of a file.

    Args:
        path: Relative or absolute path to the file to read.

    Returns:
        The file contents as a string.
    """
    return Path(path).read_text(encoding="utf-8")


def edit_file(path: str, content: str) -> dict:
    """Overwrite a file with complete new content.

    IMPORTANT: This tool overwrites the entire file on disk.
    You MUST provide the ENTIRE file content, including all existing functions and imports.
    Do NOT output only the modified function or snippet, or other functions in the file will be deleted!

    Args:
        path: Relative or absolute path to the file to write.
        content: The complete new content to write to the file (including all existing functions).

    Returns:
        A dict with keys 'status' and 'path'.
    """
    clean_content = content.strip()
    # Strip markdown code fences if present
    if clean_content.startswith("```python"):
        clean_content = clean_content[9:]
    elif clean_content.startswith("```"):
        clean_content = clean_content[3:]
    if clean_content.endswith("```"):
        clean_content = clean_content[:-3]

    # Strip full-file triple quote wrappers if present
    if clean_content.startswith('"""') and clean_content.endswith('"""') and len(clean_content) > 6:
        clean_content = clean_content[3:-3]

    clean_content = clean_content.strip()

    Path(path).write_text(clean_content, encoding="utf-8")
    return {"status": "written", "path": path}


def run_tests(*args, **kwargs) -> dict:
    """Run the full pytest test suite and return pass/fail status plus output.

    Returns:
        A dict with keys:
            'passed' (bool): True if all tests passed (exit code 0).
            'output' (str): Combined stdout + stderr from pytest.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "passed": result.returncode == 0,
        "output": result.stdout + result.stderr,
    }


# ---------------------------------------------------------------------------
# Tool registry — used by issue_resolver.py to dispatch tool calls by name
# ---------------------------------------------------------------------------
TOOL_REGISTRY: dict = {
    "read_file": read_file,
    "edit_file": edit_file,
    "run_tests": run_tests,
}
