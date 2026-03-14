#!/usr/bin/env python3
"""
Agent CLI — Call an LLM from code.

Usage:
    uv run agent.py "What does REST stand for?"

Output:
    JSON to stdout: {"answer": "...", "tool_calls": []}
    Debug output to stderr.
"""

import json
import os
import sys
from pathlib import Path

import httpx


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


def call_lllm(question: str, config: dict[str, str]) -> str:
    """Call the LLM API and return the answer."""
    url = f"{config['api_base']}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer concisely and accurately.",
            },
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
    }

    print(f"Calling LLM at {url}...", file=sys.stderr)

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"Error: Unexpected API response format: {e}", file=sys.stderr)
        print(f"Response: {data}", file=sys.stderr)
        sys.exit(1)

    print(f"Got answer from LLM", file=sys.stderr)
    return answer


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    # Load configuration
    load_env()
    config = get_llm_config()

    # Call LLM
    answer = call_lllm(question, config)

    # Output result as JSON
    result = {"answer": answer, "tool_calls": []}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
