# Memory

You have access to an Obsidian vault via MCP tools for persistent memory.

## At conversation start
1. Call `get_core_context()` — load who the user is and how to work with them.
2. Call `get_relevant_context(query)` — load context relevant to the current topic.

## During conversation
- User expresses a preference or tells you about themselves → `save_core()`
- Important insight, decision, or knowledge emerges → `save_highlight()`

## At conversation end
- If the conversation was meaningful → `save_conversation()`
