"""MCP tool wrappers for memory operations."""

from fastmcp import FastMCP

from app.domain.interfaces.memory import IMemoryService
from app.domain.interfaces.performance import IPerformanceService
from app.domain.models.conversation_note import ConversationSummary
from app.domain.models.core_note import CoreNote
from app.domain.models.highlight_note import HighlightNote
from app.tools.base import BaseTools


class MemoryTools(BaseTools):
    def __init__(
        self,
        memory: IMemoryService,
        mcp: FastMCP,
        performance_service: IPerformanceService | None = None,
        agent_name: str = "obsidian-mcp",
        model: str = "unknown",
    ) -> None:
        super().__init__(performance_service, agent_name, model)
        self._memory = memory
        mcp.tool()(self._wrap(self.get_core_context))
        mcp.tool()(self._wrap(self.get_relevant_context))
        mcp.tool()(self._wrap(self.save_highlight))
        mcp.tool()(self._wrap(self.save_core))
        mcp.tool()(self._wrap(self.save_conversation))
        mcp.tool()(self._wrap(self.rebuild_index))

    def get_core_context(self) -> str:
        """Load core context — always call at conversation start."""
        notes = self._memory.get_core_context()
        if not notes:
            return "No core context found."
        return "\n\n---\n\n".join(notes)

    def get_relevant_context(self, query: str, project: str | None = None) -> str:
        """Search for relevant memory by query. Scores by frontmatter match."""
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
        """Save an insight, decision or knowledge piece to highlights."""
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
        """Save persistent context about the user to core memory."""
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
        """Save a conversation summary with key points."""
        note = ConversationSummary(
            title=title,
            key_points=key_points,
            full_content=full_content,
            project=project,
        )
        path = self._memory.save_conversation(note)
        return f"Saved conversation: {path}"

    def rebuild_index(self) -> str:
        """Rebuild MEMORY.md index from all memory files."""
        content = self._memory.rebuild_index()
        lines = content.splitlines()
        return f"Index rebuilt: {len(lines)} lines"
