"""MCP tool wrappers for productivity operations."""

from pathlib import Path

from fastmcp import FastMCP

from app.domain.interfaces.vault import IVaultService
from app.services.productivity import ProductivityService


class ProductivityTools:
    def __init__(
        self, productivity: ProductivityService, vault: IVaultService, mcp: FastMCP
    ) -> None:
        self._productivity = productivity
        self._vault = vault
        mcp.tool()(self.get_status)
        mcp.tool()(self.create_daily_note)
        mcp.tool()(self.generate_moc)
        mcp.tool()(self.search_vault)
        mcp.tool()(self.get_note)

    def get_status(self) -> str:
        """Return vault root, memory dir, and tasks dir with index health.

        Call at conversation start before using any other tools — confirms which vault
        is active and that MEMORY.md and TASKS.md indexes exist. If an index is missing,
        call rebuild_index or rebuild_tasks_index before proceeding.
        """
        vault = self._vault
        tasks_index = vault.tasks_path / "TASKS.md"
        memory_index = vault.memory_path / "MEMORY.md"
        lines = [
            f"vault: {vault.root}",
            f"memory: {vault.memory_path} ({'ok' if vault.exists(memory_index) else 'no index'})",
            f"tasks: {vault.tasks_path} ({'ok' if vault.exists(tasks_index) else 'no index'})",
        ]
        return "\n".join(lines)

    def create_daily_note(self, content: str | None = None) -> str:
        """Append content to today's daily note, creating it if it doesn't exist."""
        path = self._productivity.create_daily_note(content)
        return f"Daily note: {path}"

    def generate_moc(self, folder: str) -> str:
        """Generate Map of Content for a vault folder."""
        content = self._productivity.generate_moc(folder)
        return f"MOC generated:\n{content}"

    def search_vault(self, query: str) -> str:
        """Full-text search across all vault markdown files. Returns up to 20 matches.

        Use for exploratory search when you don't know where information is stored.
        For memory retrieval by topic, prefer get_relevant_context — it's scored by relevance.
        For reading a specific known file, use get_note instead.
        """
        results = self._vault.search_content(query)
        if not results:
            return "No results found."
        lines: list[str] = []
        for path, context in results[:20]:
            lines.append(f"- {path}: {context}")
        return "\n".join(lines)

    def get_note(self, path: str) -> str:
        """Read a vault file by path relative to the vault root.

        Use when you have an exact path (e.g. from search_vault results).
        path example: "tasks/obsidian-mcp/improve-mcp-tool-descriptions.md"
        """
        return self._vault.read(self._vault.root / Path(path))
