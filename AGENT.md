# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) and answers questions. It is the foundation for more advanced agent capabilities that will be added in subsequent tasks.

## Architecture

```
User question → agent.py → LLM API → JSON answer
```

### Components

1. **agent.py** — Main CLI script
   - Parses command-line arguments
   - Loads LLM configuration from `.env.agent.secret`
   - Sends requests to the LLM API
   - Outputs structured JSON response

2. **.env.agent.secret** — Configuration file (gitignored)
   - `LLM_API_KEY` — API key for authentication
   - `LLM_API_BASE` — Base URL of the LLM API
   - `LLM_MODEL` — Model name to use

## LLM Provider

**Provider:** Qwen Code API (self-hosted on VM)

**Model:** `qwen3-coder-plus`

**Why Qwen Code:**
- 1000 free requests per day
- Works from Russia without restrictions
- No credit card required
- OpenAI-compatible API

## Usage

### Basic Usage

```bash
uv run agent.py "What does REST stand for?"
```

### Output Format

The agent outputs a single JSON line to stdout:

```json
{"answer": "Representational State Transfer.", "tool_calls": []}
```

- `answer` — The LLM's response to the question
- `tool_calls` — Empty array (will be populated in Task 2 when tools are added)

### Error Handling

- All debug/progress output goes to **stderr**
- Only valid JSON goes to **stdout**
- Exit code 0 on success, 1 on error
- Timeout: 60 seconds

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.agent.example .env.agent.secret
   ```

2. Edit `.env.agent.secret` and fill in:
   - `LLM_API_KEY` — Your Qwen Code API key
   - `LLM_API_BASE` — Your VM's API endpoint (e.g., `http://<vm-ip>:8080/v1`)
   - `LLM_MODEL` — Model name (default: `qwen3-coder-plus`)

## Testing

Run the regression test:

```bash
uv run pytest tests/test_agent.py -v
```

The test verifies:
- `agent.py` runs successfully
- Output is valid JSON
- `answer` field exists and is non-empty
- `tool_calls` field exists and is an empty list

## Files

| File | Description |
|------|-------------|
| `agent.py` | Main CLI script |
| `.env.agent.secret` | LLM configuration (gitignored) |
| `plans/task-1.md` | Implementation plan |
| `tests/test_agent.py` | Regression test |
| `AGENT.md` | This documentation |

## Next Steps

In Task 2, the agent will be extended with:
- Tools for reading files (`read_file`)
- Tools for listing directories (`list_files`)
- Tools for querying the backend API (`query_api`)
- An agentic loop to use tools iteratively
