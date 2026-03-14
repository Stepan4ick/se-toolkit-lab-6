# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) and answers questions using an **agentic loop**. It has tools to read files and list directories, allowing it to navigate the project wiki and find information autonomously.

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
   - Loads LLM configuration from `.env.agent.secret`
   - Implements tools: `read_file`, `list_files`
   - Executes agentic loop: call LLM → execute tools → repeat
   - Outputs structured JSON response

2. **.env.agent.secret** — Configuration file (gitignored)
   - `LLM_API_KEY` — API key for authentication
   - `LLM_API_BASE` — Base URL of the LLM API
   - `LLM_MODEL` — Model name to use

3. **Tools**
   - `read_file(path)` — Read file contents with path security
   - `list_files(path)` — List directory contents with path security

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

1. **Send question to LLM** — Include tool schemas in the request
2. **Check for tool calls** — If LLM requests tools, execute them
3. **Feed results back** — Append tool results as `tool` role messages
4. **Repeat** — Continue until LLM provides final answer or max 10 iterations
5. **Output JSON** — Return answer, source, and tool call history

### System Prompt Strategy

The system prompt instructs the LLM to:
- Use `list_files` to discover what files exist
- Use `read_file` to find specific information
- Always include source references in the final answer
- Call tools iteratively until it has enough information

## Tool Security

Both tools validate paths to prevent directory traversal attacks:
- Reject absolute paths (starting with `/`)
- Reject `..` components
- Verify resolved path is within project root
- Use `Path.resolve()` for canonical path resolution

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
- `source` — File path (and optional section anchor) where answer was found
- `tool_calls` — Array of all tool calls with arguments and results

### Error Handling

- All debug/progress output goes to **stderr**
- Only valid JSON goes to **stdout**
- Exit code 0 on success, 1 on error
- Timeout: 60 seconds per LLM call
- Max 10 tool call iterations

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.agent.example .env.agent.secret
   ```

2. Edit `.env.agent.secret` and fill in:
   - `LLM_API_KEY` — Your Qwen Code API key
   - `LLM_API_BASE` — Your VM's API endpoint
   - `LLM_MODEL` — Model name

## Testing

Run the regression tests:

```bash
uv run pytest tests/test_agent.py -v
```

Tests verify:
1. Valid JSON output with required fields
2. `read_file` tool usage for wiki questions
3. `list_files` tool usage for directory questions

## Files

| File | Description |
|------|-------------|
| `agent.py` | Main CLI script with agentic loop |
| `.env.agent.secret` | LLM configuration (gitignored) |
| `plans/task-1.md` | Task 1 implementation plan |
| `plans/task-2.md` | Task 2 implementation plan |
| `tests/test_agent.py` | Regression tests |
| `AGENT.md` | This documentation |

## Lessons Learned

### Tool Schema Design
- Clear, descriptive tool names help the LLM choose correctly
- Parameter descriptions should include examples
- Tool descriptions should explain *when* to use each tool

### Path Security
- Always validate and resolve paths before accessing files
- Use `Path.resolve()` to get canonical paths
- Check that resolved path is within allowed directory

### Agentic Loop
- Limit iterations to prevent infinite loops
- Log each iteration for debugging
- Handle both `tool_calls` and `content` in LLM responses

## Next Steps

In Task 3, the agent will be extended with:
- `query_api` tool to query the backend API
- Authentication for API calls using `LMS_API_KEY`
- Support for data-dependent questions
- Benchmark evaluation against 10 questions
