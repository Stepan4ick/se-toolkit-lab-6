# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) and answers questions using an **agentic loop**. It has three tools:
- `read_file` — Read files from the project repository
- `list_files` — List directory contents
- `query_api` — Query the backend API with authentication

The agent can navigate documentation, read source code, and query live data to answer questions accurately.

## Architecture

```
User question ──▶ LLM ──▶ tool call? ──yes──▶ execute tool ──▶ back to LLM
                         │
                         no
                         │
                         ▼
                    JSON output
```

### Components

1. **agent.py** — Main CLI script with agentic loop
   - Parses command-line arguments
   - Loads configuration from `.env.agent.secret` and `.env.docker.secret`
   - Implements three tools with security validation
   - Executes agentic loop: call LLM → execute tools → repeat (max 10 iterations)
   - Outputs structured JSON response

2. **.env.agent.secret** — LLM configuration (gitignored)
   - `LLM_API_KEY` — API key for LLM authentication
   - `LLM_API_BASE` — Base URL of the LLM API
   - `LLM_MODEL` — Model name to use

3. **.env.docker.secret** — Backend API configuration (gitignored)
   - `LMS_API_KEY` — API key for backend authentication
   - Backend URLs and database credentials

4. **Tools**
   - `read_file(path)` — Read file contents with path security
   - `list_files(path)` — List directory contents with path security
   - `query_api(method, path, body)` — Query HTTP API with Bearer auth

## LLM Provider

**Provider:** Qwen Code API (self-hosted on VM)

**Model:** `coder-model`

**Why Qwen Code:**
- 1000 free requests per day
- Works from Russia without restrictions
- No credit card required
- OpenAI-compatible API

## Agentic Loop

The agent uses an iterative loop to answer questions:

1. **Send question to LLM** — Include all 3 tool schemas in the request
2. **Check for tool calls** — If LLM requests tools, execute them
3. **Feed results back** — Append tool results as `tool` role messages
4. **Repeat** — Continue until LLM provides final answer or max 10 iterations
5. **Output JSON** — Return answer, source, and tool call history

### System Prompt Strategy

The system prompt guides the LLM on tool selection:

- **Wiki/documentation questions** → `list_files` to discover, then `read_file` for details
- **Source code questions** → `read_file` to read relevant source files
- **Data-dependent questions** (counts, statistics) → `query_api` to get current data
- **API behavior questions** (status codes, errors) → `query_api` to test endpoints
- **Bug diagnosis** → `query_api` first to see the error, then `read_file` to examine source

## Tool Security

### Path Validation (read_file, list_files)

Both file tools validate paths to prevent directory traversal attacks:
- Reject absolute paths (starting with `/` or `\`)
- Reject `..` components (directory traversal)
- Verify resolved path is within project root using `Path.resolve()`

### API Security (query_api)

The query_api tool enforces:
- Only relative paths allowed (no `http://` URLs)
- Bearer token authentication using `LMS_API_KEY`
- Timeout of 30 seconds per request
- Graceful error handling for connection failures

## Usage

### Basic Usage

```bash
uv run agent.py "How do you resolve a merge conflict?"
```

### Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "..."
    }
  ]
}
```

- `answer` — The LLM's final response
- `source` — File path or API endpoint where answer was found (optional for API questions)
- `tool_calls` — Array of all tool calls with arguments and results

### Error Handling

- All debug/progress output goes to **stderr**
- Only valid JSON goes to **stdout**
- Exit code 0 on success, 1 on error
- Timeout: 60 seconds per LLM call, 30 seconds per API call
- Max 10 tool call iterations

## Configuration

### LLM Configuration (.env.agent.secret)

```bash
cp .env.agent.example .env.agent.secret
```

Edit `.env.agent.secret`:
- `LLM_API_KEY` — Your Qwen Code API key
- `LLM_API_BASE` — Your VM's API endpoint (e.g., `http://<vm-ip>:42005/v1`)
- `LLM_MODEL` — Model name (e.g., `coder-model`)

### Backend Configuration (.env.docker.secret)

```bash
cp .env.docker.example .env.docker.secret
```

Edit `.env.docker.secret`:
- `LMS_API_KEY` — Backend API key (used by `query_api` for authentication)

> **Important:** Two distinct keys:
> - `LLM_API_KEY` authenticates with the LLM provider
> - `LMS_API_KEY` authenticates with the backend API
> 
> Never mix them up or hardcode them in `agent.py`.

## Testing

Run the regression tests:

```bash
uv run pytest tests/test_agent.py -v
```

Tests verify:
1. Valid JSON output with required fields
2. `read_file` tool usage for wiki questions
3. `list_files` tool usage for directory questions
4. `read_file` tool usage for source code questions (FastAPI detection)
5. `query_api` tool usage for data-dependent questions

## Benchmark Evaluation

Run the local benchmark:

```bash
uv run run_eval.py
```

The benchmark tests 10 questions across all classes:
- Wiki lookup (merge conflicts, SSH)
- System facts (framework, status codes)
- Data queries (item count)
- Bug diagnosis (ZeroDivisionError, TypeError)
- Reasoning (request lifecycle, ETL idempotency)

## Files

| File | Description |
|------|-------------|
| `agent.py` | Main CLI script with agentic loop |
| `.env.agent.secret` | LLM configuration (gitignored) |
| `.env.docker.secret` | Backend API configuration (gitignored) |
| `plans/task-1.md` | Task 1 implementation plan |
| `plans/task-2.md` | Task 2 implementation plan |
| `plans/task-3.md` | Task 3 implementation plan |
| `tests/test_agent.py` | Regression tests (5 tests) |
| `AGENT.md` | This documentation |

## Lessons Learned

### Tool Design

1. **Clear descriptions matter** — The LLM chooses tools based on descriptions. Be specific about when to use each tool.

2. **Parameter examples help** — Include example values in parameter descriptions (e.g., `/items/`, `/analytics/completion-rate`).

3. **Security is essential** — Always validate paths and URLs. Never trust user input from the LLM.

### Agentic Loop

1. **Iteration limit prevents infinite loops** — Set `max_iterations = 10` to avoid runaway tool calling.

2. **Log everything to stderr** — Debug output helps diagnose why the LLM made certain tool choices.

3. **Handle null content** — When LLM returns tool calls, `content` may be `null`. Use `(msg.get("content") or "")` instead of default.

### API Integration

1. **Authentication is critical** — The `query_api` tool must include `Authorization: Bearer <LMS_API_KEY>` header.

2. **Environment variables for flexibility** — Read `AGENT_API_BASE_URL` from environment so the autochecker can inject different values.

3. **Graceful error handling** — Connection errors should return a helpful message, not crash.

### Benchmark Iteration

1. **Start simple** — Get basic questions working first (wiki lookup, framework detection).

2. **Debug tool by tool** — If a question fails, check which tool was called and why.

3. **System prompt tuning** — Small changes to the system prompt can significantly improve tool selection.

## Final Eval Score

| Question Type | Count | Status |
|--------------|-------|--------|
| Wiki lookup | 2 | ✅ |
| System facts | 2 | ✅ |
| Data queries | 2 | ✅ |
| Bug diagnosis | 2 | ✅ |
| Reasoning | 2 | ✅ |

**Total: 10/10 passing** (after iteration on system prompt and tool descriptions)

## Next Steps

The agent is complete for Task 3. Future improvements could include:
- Support for multi-step reasoning with explicit chain-of-thought
- Caching for repeated file reads
- Parallel tool execution for independent queries
- Support for image files and binary content
