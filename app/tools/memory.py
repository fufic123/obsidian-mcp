"""MCP tool wrappers for memory operations."""

from fastmcp import FastMCP

from app.domain.interfaces.memory import IMemoryService
from app.domain.models.conversation_note import ConversationSummary
from app.domain.models.core_note import CoreNote
from app.domain.models.highlight_note import HighlightNote


class MemoryTools:
    def __init__(self, memory: IMemoryService, mcp: FastMCP) -> None:
        self._memory = memory
        mcp.tool()(self.get_core_context)
        mcp.tool()(self.get_relevant_context)
        mcp.tool()(self.save_highlight)
        mcp.tool()(self.save_core)
        mcp.tool()(self.save_conversation)
        mcp.tool()(self.rebuild_index)

    def get_core_context(self) -> str:
        """Load the user's persistent profile — call at every conversation start.

        Returns all core notes: who the user is, their preferences, and constraints.
        Call this before get_relevant_context so you have user context before searching.
        """
        notes = self._memory.get_core_context()
        if not notes:
            return "No core context found."
        return "\n\n---\n\n".join(notes)

    def get_relevant_context(self, query: str, project: str | None = None) -> str:
        """Search highlights and conversation summaries by topic.

        Call after get_core_context with 1-3 short keywords matching the current topic.
        Use keywords, not full sentences — e.g. "auth refactor" not "how did we refactor auth".
        project: narrow results to a specific project.
        Do NOT use for task lookup — use list_tasks / get_task instead.
        """
        results = self._memory.get_relevant_context(query, project)
        if not results:
            return "No relevant context found."
        lines: list[str] = []
        for r in results:
            tags = ", ".join(r.tags) if r.tags else ""
            lines.append(
                f"- **{r.name}** ({r.note_type}) — {r.description}"
                + (f" [{tags}]" if tags else "")
                + f" (score: {r.score:.1f})"
                + f"\n  Path: {r.path}"
            )
        return "\n".join(lines)

    def save_highlight(
        self,
        name: str,
        description: str,
        content: str,
        tags: list[str] | None = None,
        project: str | None = None,
    ) -> str:
        """Save an insight, decision, or domain knowledge worth remembering across conversations.

        Use when: a technical decision was made, a pattern was discovered, or something
        non-obvious emerged that would help future conversations on this topic.
        NOT for user preferences → use save_core.
        NOT for conversation summaries → use save_conversation.

        description: one sentence — what this note is about (used for search scoring).
        content: full insight with enough context to be self-contained in a future conversation.
        tags: keywords for retrieval (e.g. ["auth", "postgres"]).
        project: scope to a project so get_relevant_context(project=...) can filter it.
        """
        note = HighlightNote(
            name=name,
            description=description,
            content=content,
            tags=tags or [],
            project=project,
        )
        path = self._memory.save_highlight(note)
        return f"Saved highlight: {path}"

    def save_core(self, name: str, description: str, content: str) -> str:
        """Save a persistent fact about the user — preferences, constraints, or identity.

        Use when: the user states how they like to work, a tool/language they use,
        a team they belong to, or a constraint that applies to all future conversations.
        NOT for project insights → use save_highlight.
        NOT for conversation summaries → use save_conversation.

        Overwrites any existing core note with the same name — use a stable name
        (e.g. "communication-preferences", "tech-stack") so updates replace, not duplicate.
        """
        note = CoreNote(name=name, description=description, content=content)
        path = self._memory.save_core(note)
        return f"Saved core note: {path}"

    def save_conversation(
        self,
        title: str,
        key_points: list[str],
        full_content: str,
        project: str | None = None,
    ) -> str:
        """Save a summary of this conversation — call ONLY at the end of the session.

        Do NOT call mid-conversation or after small talk / one-off questions.
        Call when: meaningful work was done, decisions were made, or context was built
        that would help a future conversation pick up where this one left off.

        key_points: 3-5 short standalone facts (each readable without the full summary).
        full_content: prose summary — what was discussed, what was decided, what changed.
        project: associate with a project so get_relevant_context(project=...) can find it.
        """
        note = ConversationSummary(
            title=title,
            key_points=key_points,
            full_content=full_content,
            project=project,
        )
        path = self._memory.save_conversation(note)
        return f"Saved conversation: {path}"

    def rebuild_index(self) -> str:
        """Regenerate MEMORY.md from all memory files — call only when explicitly asked.

        All save_* tools rebuild the index automatically. Only call this after manually
        editing vault files outside the MCP, or if the index appears stale.
        """
        content = self._memory.rebuild_index()
        lines = content.splitlines()
        return f"Index rebuilt: {len(lines)} lines"
