"""MCP tool wrappers for memory operations."""

from fastmcp import FastMCP

from app.domain.interfaces.memory import IMemoryService


def register_memory_tools(mcp: FastMCP, memory: IMemoryService) -> None:
    """Register memory-related MCP tools."""

    @mcp.tool()
    def get_core_context() -> str:
        """Load core context — always call at conversation start."""
        notes = memory.get_core_context()
        if not notes:
            return "No core context found."
        return "\n\n---\n\n".join(notes)

    @mcp.tool()
    def get_relevant_context(query: str, project: str | None = None) -> str:
        """Search for relevant memory by query. Scores by frontmatter match."""
        results = memory.get_relevant_context(query, project)
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

    @mcp.tool()
    def save_highlight(
        name: str,
        description: str,
        content: str,
        tags: list[str] | None = None,
        project: str | None = None,
    ) -> str:
        """Save an insight, decision or knowledge piece to highlights."""
        from app.domain.models.notes import HighlightNote

        note = HighlightNote(
            name=name,
            description=description,
            content=content,
            tags=tags or [],
            project=project,
        )
        path = memory.save_highlight(note)
        return f"Saved highlight: {path}"

    @mcp.tool()
    def save_core(name: str, description: str, content: str) -> str:
        """Save persistent context about the user to core memory."""
        from app.domain.models.notes import CoreNote

        note = CoreNote(name=name, description=description, content=content)
        path = memory.save_core(note)
        return f"Saved core note: {path}"

    @mcp.tool()
    def save_conversation(
        title: str,
        key_points: list[str],
        full_content: str,
        project: str | None = None,
    ) -> str:
        """Save a conversation summary with key points."""
        from app.domain.models.notes import ConversationSummary

        note = ConversationSummary(
            title=title,
            key_points=key_points,
            full_content=full_content,
            project=project,
        )
        path = memory.save_conversation(note)
        return f"Saved conversation: {path}"

    @mcp.tool()
    def rebuild_index() -> str:
        """Rebuild MEMORY.md index from all memory files."""
        content = memory.rebuild_index()
        lines = content.splitlines()
        return f"Index rebuilt: {len(lines)} lines"
