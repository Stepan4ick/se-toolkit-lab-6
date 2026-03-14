import json
import os
import sys
from pathlib import Path

import httpx


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _load_env(filepath: str) -> None:
    """Load key=value pairs from a file into os.environ."""
    p = Path(filepath)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env(".env.agent.secret")
_load_env(".env.docker.secret")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/llama-4-scout:free")
LMS_API_KEY = os.environ.get("LMS_API_KEY", "")
AGENT_API_BASE_URL = os.environ.get("AGENT_API_BASE_URL", "http://localhost:42002")

PROJECT_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def tool_read_file(path: str) -> str:
    """Read a file from the project directory."""
    resolved = (PROJECT_ROOT / path).resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT)):
        return "Error: path traversal not allowed"
    if not resolved.is_file():
        return f"Error: file not found: {path}"
    try:
        return resolved.read_text(encoding="utf-8", errors="replace")[:30000]
    except Exception as e:
        return f"Error reading file: {e}"


def tool_list_files(path: str) -> str:
    """List files and directories at a given path."""
    resolved = (PROJECT_ROOT / path).resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT)):
        return "Error: path traversal not allowed"
    if not resolved.is_dir():
        return f"Error: directory not found: {path}"
    try:
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in resolved.iterdir() if not p.name.startswith("."))
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


def tool_query_api(method: str, path: str, body: str | None = None, authenticated: bool = True) -> str:
    """Query the backend API."""
    url = f"{AGENT_API_BASE_URL}{path}"
    headers = {}
    if authenticated and LMS_API_KEY:
        headers["Authorization"] = f"Bearer {LMS_API_KEY}"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.request(method, url, headers=headers, content=body if body else None)
            return json.dumps({"status_code": resp.status_code, "body": resp.text[:5000]})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": f"Error: {e}"})


TOOLS = {
    "read_file": tool_read_file,
    "list_files": tool_list_files,
    "query_api": tool_query_api,
}
