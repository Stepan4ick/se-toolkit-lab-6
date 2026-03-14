# Plan: Task 1 — Call an LLM from Code

## LLM Provider and Model

**Provider:** Qwen Code API (self-hosted on VM)

**Model:** `qwen3-coder-plus`

**Reasoning:**
- Qwen Code provides 1000 free requests per day
- Works from Russia without restrictions
- No credit card required
- OpenAI-compatible API endpoint

## Configuration

The agent will read configuration from `.env.agent.secret`:

- `LLM_API_KEY` — API key from Qwen Code
- `LLM_API_BASE` — Base URL (e.g., `http://<vm-ip>:<port>/v1`)
- `LLM_MODEL` — Model name (`qwen3-coder-plus`)

## Agent Architecture

### Input

Command-line argument: `uv run agent.py "What does REST stand for?"`

### Flow

1. Parse command-line argument (question string)
2. Load environment variables from `.env.agent.secret`
3. Build OpenAI-compatible request:
   - System prompt: "You are a helpful assistant. Answer concisely and accurately."
   - User message: the question
4. Send POST request to `LLM_API_BASE/chat/completions`
5. Parse JSON response
6. Output result to stdout as JSON:
   ```json
   {"answer": "...", "tool_calls": []}
   ```

### Output

- **stdout:** Single JSON line with `answer` and `tool_calls`
- **stderr:** All debug/progress messages
- **Exit code:** 0 on success

## Error Handling

- Network errors → print to stderr, exit code 1
- Invalid API response → print to stderr, exit code 1
- Missing environment variables → print to stderr, exit code 1
- Timeout (>60 seconds) → print to stderr, exit code 1

## Testing

Create `tests/test_agent.py`:

1. Run `agent.py` as subprocess with a test question
2. Parse stdout as JSON
3. Assert `answer` field exists and is non-empty string
4. Assert `tool_calls` field exists and is empty list

## Files to Create

1. `plans/task-1.md` — this plan
2. `.env.agent.secret` — LLM configuration (copy from `.env.agent.example`)
3. `agent.py` — main CLI script
4. `AGENT.md` — documentation
5. `tests/test_agent.py` — regression test

## Dependencies

- `httpx` — already in `pyproject.toml` for HTTP requests
- `python-dotenv` — may need to add for loading `.env` files, or use `os.environ`
