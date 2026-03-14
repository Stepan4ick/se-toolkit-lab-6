#!/usr/bin/env python3
"""
Agent CLI — Call an LLM from code with tools.

Usage:
    uv run agent.py "What does REST stand for?"

Output:
    JSON to stdout: {"answer": "...", "source": "...", "tool_calls": [...]}
    Debug output to stderr.
"""

import json
import os
import sys
import io
from pathlib import Path

import httpx

# Set UTF-8 encoding for stdout to handle Unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_env() -> None:
    """Load environment variables from .env.agent.secret."""
    env_file = Path(__file__).parent / ".env.agent.secret"
    if not env_file.exists():
        print(f"Error: {env_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def get_llm_config() -> dict[str, str]:
    """Get LLM configuration from environment variables."""
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")
    model = os.environ.get("LLM_MODEL")

    if not api_key:
        print("Error: LLM_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not api_base:
        print("Error: LLM_API_BASE not set", file=sys.stderr)
        sys.exit(1)
    if not model:
        print("Error: LLM_MODEL not set", file=sys.stderr)
        sys.exit(1)

    return {"api_key": api_key, "api_base": api_base, "model": model}


def validate_path(path: str, project_root: Path) -> Path:
    """Validate and resolve a relative path within project root.
    
    Security: reject absolute paths and directory traversal.
    """
    # Reject absolute paths
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError(f"Absolute paths not allowed: {path}")
    
    # Reject directory traversal
    if ".." in path.split("/") or ".." in path.split("\\"):
        raise ValueError(f"Directory traversal not allowed: {path}")
    
    # Resolve the full path
    full_path = (project_root / path).resolve()
    
    # Verify the resolved path is within project root
    try:
        full_path.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Path outside project root: {path}")
    
    return full_path


def read_file(path: str, project_root: Path) -> str:
    """Read contents of a file from the project repository."""
    try:
        full_path = validate_path(path, project_root)
        
        if not full_path.exists():
            return f"Error: File not found: {path}"
        
        if not full_path.is_file():
            return f"Error: Not a file: {path}"
        
        with open(full_path, encoding="utf-8") as f:
            return f.read()
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str, project_root: Path) -> str:
    """List files and directories at a given path."""
    try:
        full_path = validate_path(path, project_root)
        
        if not full_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not full_path.is_dir():
            return f"Error: Not a directory: {path}"
        
        entries = []
        for entry in sorted(full_path.iterdir()):
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        
        return "\n".join(entries)
    
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


def get_tool_schemas() -> list[dict]:
    """Return tool schemas for OpenAI function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a file from the project repository. Use this to find specific information in documentation or source code. Supports .md, .py, .yml, .json, and other text files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path from project root (e.g., 'wiki/git-workflow.md' or 'backend/routers/items.py')"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and directories at a given path. Use this to discover what files exist in a directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative directory path from project root (e.g., 'wiki')"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ]


def execute_tool(tool_name: str, args: dict, project_root: Path) -> str:
    """Execute a tool and return its result."""
    print(f"Executing tool: {tool_name}({args})", file=sys.stderr)
    
    if tool_name == "read_file":
        path = args.get("path", "")
        return read_file(path, project_root)
    
    elif tool_name == "list_files":
        path = args.get("path", "")
        return list_files(path, project_root)
    
    else:
        return f"Error: Unknown tool: {tool_name}"


def call_llm(question: str, config: dict[str, str], project_root: Path) -> dict:
    """Call the LLM API with agentic loop and return the result."""
    url = f"{config['api_base']}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }
    
    system_prompt = """You are a helpful documentation assistant. You can read files and list directories to find information.

When answering questions:
1. Use list_files to discover what files exist in a directory
2. Use read_file to read specific files and find the answer
3. Always include the source reference (file path) in your final answer
4. If you need to find information about a topic, start by listing files in the relevant directory

Respond with tool calls when you need to read files or list directories. When you have enough information, provide the final answer with the source."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    
    tool_calls_log = []
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"Iteration {iteration}/{max_iterations}", file=sys.stderr)
        
        payload = {
            "model": config["model"],
            "messages": messages,
            "tools": get_tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0.7,
        }
        
        print(f"Calling LLM at {url}...", file=sys.stderr)
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        
        data = response.json()
        
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            print(f"Error: Unexpected API response format: {e}", file=sys.stderr)
            print(f"Response: {data}", file=sys.stderr)
            sys.exit(1)
        
        # Check for tool calls
        tool_calls = msg.get("tool_calls")
        
        if tool_calls:
            # Execute each tool call
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name", "")
                args_str = function.get("arguments", "{}")
                
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                
                result = execute_tool(tool_name, args, project_root)
                
                # Log the tool call
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": args,
                    "result": result
                })
                
                print(f"Tool {tool_name} result: {result[:100]}...", file=sys.stderr)
                
                # Append assistant message with tool call
                messages.append({
                    "role": "assistant",
                    "content": msg.get("content"),
                    "tool_calls": tool_calls
                })
                
                # Append tool result
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                    "tool_call_id": tool_call.get("id", "")
                })
            
            # Continue loop to get next LLM response
            continue
        
        # No tool calls - we have the final answer
        answer = msg.get("content") or ""
        print(f"Got final answer from LLM", file=sys.stderr)
        
        # Extract source from answer (look for file references)
        source = extract_source(answer, tool_calls_log)
        
        return {
            "answer": answer,
            "source": source,
            "tool_calls": tool_calls_log
        }
    
    # Max iterations reached
    print("Max iterations reached", file=sys.stderr)
    source = extract_source("", tool_calls_log)
    return {
        "answer": "I reached the maximum number of tool calls (10). Here's what I found so far.",
        "source": source,
        "tool_calls": tool_calls_log
    }


def extract_source(answer: str, tool_calls_log: list) -> str:
    """Extract source reference from tool calls or answer."""
    # Look for file paths in tool calls
    for call in tool_calls_log:
        if call["tool"] == "read_file":
            path = call["args"].get("path", "")
            if path:
                # Try to find section in answer
                if "##" in answer:
                    # Extract section header
                    for line in answer.split("\n"):
                        if line.startswith("##"):
                            section = line.strip().lstrip("#").strip()
                            anchor = section.lower().replace(" ", "-").replace("'", "")
                            return f"{path}#{anchor}"
                return path
    
    return ""


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    project_root = Path(__file__).parent

    # Load configuration
    load_env()
    config = get_llm_config()

    # Call LLM with agentic loop
    result = call_llm(question, config, project_root)

    # Output result as JSON
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
