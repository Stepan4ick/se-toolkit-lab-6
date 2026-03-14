"""Regression tests for agent.py CLI."""

import json
import subprocess
import sys
from pathlib import Path


def test_agent_outputs_valid_json() -> None:
    """Test that agent.py outputs valid JSON with required fields."""
    agent_path = Path(__file__).parent.parent / "agent.py"
    test_question = "What is 2 + 2?"

    result = subprocess.run(
        [sys.executable, "-m", "uv", "run", str(agent_path), test_question],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent failed: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON output: {e}\nStdout: {result.stdout}")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert len(output["answer"]) > 0, "'answer' must not be empty"

    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be a list"
    assert output["tool_calls"] == [], "'tool_calls' must be empty for Task 1"
