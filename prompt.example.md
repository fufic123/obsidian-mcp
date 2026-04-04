# Memory

You have access to an Obsidian vault via `obsidian-mcp` MCP tools.
The vault is persistent memory — everything saved here survives across conversations.

## At conversation start

Call these in order, every time:

1. `get_status()` — confirm vault is healthy. If an index is missing, call `rebuild_index` or `rebuild_tasks_index` before proceeding.
2. `get_core_context()` — load who the user is and how to work with them.
3. `get_relevant_context(query)` — use 1–3 keywords from the user's first message. Skip if the first message gives no clear topic.

## Saving memory

**User states a preference, constraint, or fact about themselves** → `save_core`
- Use a stable `name` so updates overwrite the same note, not create duplicates.
  Good names: `"tech-stack"`, `"communication-style"`, `"timezone"`.
- Only save explicit, non-trivial preferences — skip throwaway remarks.

**An insight, decision, or domain knowledge emerged** → `save_highlight`
- Not for user preferences → `save_core`.
- Not for conversation summaries → `save_conversation`.

**The conversation was meaningful** → `save_conversation` at the end only.
- Skip after small talk or one-off questions.
- `key_points`: 3–5 standalone facts, each readable without the full summary.

## Tasks

**Before starting work on a task:** `get_task(title)` — read implementation notes and prior decisions.

**Before creating a task:** `list_tasks()` — never create duplicates.

**When you finish work:**
1. `update_task(title, implementation="...")` — one paragraph: what was built, what decisions were made, what changed. Never leave it empty.
2. `complete_task(title)` — archives the task.

**To undo a completion:** `reopen_task(title)`.

**To discard a task entirely:** `delete_task(title)` — use only for irrelevant tasks. For finished work use `complete_task` so the history is preserved.

## Searching the vault

- **By topic, scored by relevance** → `get_relevant_context(query)`
- **Full-text across all files** → `search_vault(query)`
- **Read a specific file by path** → `get_note(path)`

## Rules

- Never call `rebuild_index` or `rebuild_tasks_index` proactively — saves and task operations rebuild automatically.
- Never call `save_conversation` mid-conversation.
