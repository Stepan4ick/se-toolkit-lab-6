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
        ["uv", "run", str(agent_path), test_question],
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


def test_agent_uses_read_file_for_wiki_question() -> None:
    """Test that agent uses read_file tool for wiki questions."""
    agent_path = Path(__file__).parent.parent / "agent.py"
    test_question = "How do you resolve a merge conflict?"

    result = subprocess.run(
        ["uv", "run", str(agent_path), test_question],
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
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Check that read_file was used
    tool_names = [call["tool"] for call in output["tool_calls"]]
    assert "read_file" in tool_names, f"Expected read_file in tool_calls, got: {tool_names}"

    # Check that source references git-workflow.md
    assert "git-workflow.md" in output["source"], \
        f"Expected git-workflow.md in source, got: {output['source']}"


def test_agent_uses_list_files_for_directory_question() -> None:
    """Test that agent uses list_files tool for directory questions."""
    agent_path = Path(__file__).parent.parent / "agent.py"
    test_question = "What files are in the wiki directory?"

    result = subprocess.run(
        ["uv", "run", str(agent_path), test_question],
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
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Check that list_files was used
    tool_names = [call["tool"] for call in output["tool_calls"]]
    assert "list_files" in tool_names, f"Expected list_files in tool_calls, got: {tool_names}"
