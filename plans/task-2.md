# Plan: Task 2 — The Documentation Agent

## Overview

Extend the agent from Task 1 with tools (`read_file`, `list_files`) and an agentic loop to answer questions by reading the project wiki.

## Agentic Loop Architecture

```
Question ──▶ LLM ──▶ tool call? ──yes──▶ execute tool ──▶ back to LLM
                         │
                         no
                         │
                         ▼
                    JSON output
```

### Flow

1. Send user question + tool definitions to LLM
2. If LLM responds with `tool_calls`:
   - Execute each tool
   - Append results as `tool` role messages
   - Go to step 1
3. If LLM responds with text (no tool calls):
   - Extract final answer and source
   - Output JSON and exit
4. If >10 tool calls → stop and use whatever answer we have

## Tool Schemas

### `read_file`

**Description:** Read contents of a file from the project repository.

**Parameters:**
- `path` (string, required) — relative path from project root

**Returns:** File contents as string, or error message if file doesn't exist.

**Security:** Reject paths with `../` traversal or absolute paths.

### `list_files`

**Description:** List files and directories at a given path.

**Parameters:**
- `path` (string, required) — relative directory path from project root

**Returns:** Newline-separated listing of entries.

**Security:** Reject paths with `../` traversal or absolute paths.

## System Prompt

The system prompt will instruct the LLM to:
1. Use `list_files` to discover wiki files when needed
2. Use `read_file` to find specific information
3. Include source reference (file path + section anchor) in the final answer
4. Call tools iteratively until it has enough information

## Path Security

Both tools must validate paths:
- Reject absolute paths (starting with `/`)
- Reject `..` components (directory traversal)
- Only allow paths within project root
- Use `Path.resolve()` to verify final path is within project

## Output Format

```json
{
  "answer": "How to resolve merge conflict...",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Implementation Steps

1. Add tool functions (`read_file`, `list_files`) with path validation
2. Build tool schemas for OpenAI function calling
3. Implement agentic loop in `call_llm()`
4. Update output format to include `source` and `tool_calls`
5. Update system prompt
6. Add 2 regression tests
7. Update `AGENT.md`

## Testing Strategy

**Test 1:** Question about merge conflict resolution
- Input: `"How do you resolve a merge conflict?"`
- Expected: `read_file` in tool_calls, `wiki/git-workflow.md` in source

**Test 2:** Question about wiki files
- Input: `"What files are in the wiki?"`
- Expected: `list_files` in tool_calls

## Dependencies

- `httpx` — already available for HTTP requests
- `os`, `sys`, `json` — standard library
- `pathlib.Path` — for path handling
