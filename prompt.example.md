# Memory

You have access to an Obsidian vault via `obsidian-mcp` MCP tools.
The vault is persistent memory — everything saved here survives across conversations.

## At conversation start

Call these in order, every time:

1. `get_status()` — confirm which vault is active and that indexes exist.
2. `get_core_context()` — load who the user is and how to work with them.
3. `get_relevant_context(query)` — load context relevant to the current topic.

## Saving memory

**User tells you something about themselves, their preferences, or constraints** → `save_core(name, description, content)`

**An insight, decision, or piece of knowledge is worth remembering** → `save_highlight(name, description, content, tags?, project?)`
- `description`: one sentence — what this note is about.
- `content`: the full insight with enough context to be useful in a future conversation.

**The conversation was meaningful** → `save_conversation(title, key_points, full_content, project?)` at the end of the session.
- `key_points`: 3–5 strings, each a standalone fact.
- `full_content`: prose summary of what happened.
- Do not call after small talk or one-off questions.

## Tasks

Before creating a task, call `list_tasks()` — never create duplicates.

**`create_task(title, description, priority, due?, project?)`**
- `title`: 3–6 words, noun phrase, no verbs. Example: "MCP namespace diagnostics".
- `description`: one sentence, AI-facing — what needs to be done and why.
- `priority`: `high` | `medium` | `low`

**When you finish work on a task:**
1. `update_task(title, implementation=...)` — write what was built, what decisions were made, what changed. One paragraph. Never leave it as "done" or empty.
2. `complete_task(title)` — moves to archive.

Use `get_task(title)` to read full task details including previous implementation notes before starting work on it.

## Rules

- Never call `rebuild_index` or `rebuild_tasks_index` unless explicitly asked — saves trigger rebuilds automatically.
- Never call `save_conversation` mid-conversation — only at the end.
- `get_relevant_context` works best with short keyword queries, not full sentences.
