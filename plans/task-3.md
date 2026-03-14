# Plan: Task 3 — The System Agent

## Overview

Extend the agent from Task 2 with a `query_api` tool to query the deployed backend API. This enables the agent to answer data-dependent questions (e.g., "How many items are in the database?") and diagnose bugs by observing actual API behavior.

## New Tool: `query_api`

**Description:** Call the backend API with authentication.

**Parameters:**
- `method` (string, required) — HTTP method (GET, POST, etc.)
- `path` (string, required) — API path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (string, optional) — JSON request body for POST/PUT requests

**Returns:** JSON string with `status_code` and `body`.

**Authentication:** Use `LMS_API_KEY` from `.env.docker.secret` in the `Authorization: Bearer` header.

**Security:**
- Only allow relative paths (no `http://` or absolute URLs)
- Use `AGENT_API_BASE_URL` from environment (default: `http://localhost:42002`)

## Environment Variables

The agent must read all configuration from environment variables:

| Variable             | Purpose                                      | Source                  |
|---------------------|----------------------------------------------|-------------------------|
| `LLM_API_KEY`       | LLM provider API key                         | `.env.agent.secret`     |
| `LLM_API_BASE`      | LLM API endpoint URL                         | `.env.agent.secret`     |
| `LLM_MODEL`         | Model name                                   | `.env.agent.secret`     |
| `LMS_API_KEY`       | Backend API key for `query_api` auth         | `.env.docker.secret`    |
| `AGENT_API_BASE_URL`| Base URL for `query_api`                     | Optional, default localhost |

**Important:** The autochecker runs with different credentials and backend URL. Never hardcode these values.

## System Prompt Updates

Update the system prompt to guide the LLM on when to use each tool:

- **Wiki questions** (how-to, concepts) → `read_file`, `list_files`
- **System facts** (framework, ports, status codes) → `read_file` (source code) or `query_api`
- **Data queries** (item count, scores) → `query_api`
- **Bug diagnosis** → `query_api` first to see error, then `read_file` to examine source

## Agentic Loop

The loop remains the same as Task 2, just with an additional tool:

1. Send question + all 3 tool schemas to LLM
2. If LLM calls a tool → execute it, feed result back
3. Continue until final answer or max 10 iterations
4. Output JSON with `answer`, `source` (optional for API questions), `tool_calls`

## Output Format

```json
{
  "answer": "There are 120 items in the database.",
  "source": "",
  "tool_calls": [
    {
      "tool": "query_api",
      "args": {"method": "GET", "path": "/items/"},
      "result": "{\"status_code\": 200, \"body\": {...}}"
    }
  ]
}
```

Note: `source` is now optional — API questions may not have a wiki source.

## Implementation Steps

1. Add `query_api` function with authentication
2. Add `query_api` schema to `get_tool_schemas()`
3. Update `execute_tool()` to handle `query_api`
4. Update system prompt to guide tool selection
5. Update `call_llm()` to read `LMS_API_KEY` and `AGENT_API_BASE_URL`
6. Create `plans/task-3.md`
7. Add 2 regression tests for `query_api`
8. Update `AGENT.md`
9. Run `run_eval.py` and iterate until all 10 questions pass

## Testing Strategy

**Test 1:** Static system fact
- Question: `"What framework does the backend use?"`
- Expected: `read_file` in tool_calls (reads `backend/app/main.py`)

**Test 2:** Data-dependent query
- Question: `"How many items are in the database?"`
- Expected: `query_api` in tool_calls with GET `/items/`

## Benchmark Evaluation

Run the local benchmark:
```bash
uv run run_eval.py
```

10 questions across all classes:
- Wiki lookup (2 questions)
- System facts (2 questions)
- Data queries (2 questions)
- Bug diagnosis (2 questions)
- Reasoning (2 questions)

Iterate on:
- System prompt clarity
- Tool descriptions
- Error handling

## Known API Endpoints

Based on `backend/app/main.py`:
- `/items/` — List items (GET), Create item (POST)
- `/items/{id}/interactions/` — Add interaction (POST)
- `/learners/` — List learners (GET)
- `/pipeline/run/` — Run ETL pipeline (POST)
- `/analytics/completion-rate` — Get completion rate (GET)
- `/analytics/top-learners` — Get top learners (GET)

All endpoints require `Authorization: Bearer <LMS_API_KEY>`.

## Potential Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent doesn't call `query_api` for data questions | System prompt doesn't distinguish data vs static questions | Clarify when to use each tool |
| `query_api` returns 401 | Missing or wrong API key | Check `LMS_API_KEY` is loaded from `.env.docker.secret` |
| Agent crashes on API error | Not handling non-200 responses | Return status_code in result, let LLM reason about it |
| Agent loops on same tool call | LLM doesn't see progress | Include full result in tool response |

## Success Criteria

- [ ] `query_api` tool works with authentication
- [ ] Agent answers data-dependent questions correctly
- [ ] Agent diagnoses bugs from API errors
- [ ] `run_eval.py` passes all 10 local questions
- [ ] 2 new regression tests pass
- [ ] `AGENT.md` updated (200+ words)
