"""MCP tool wrappers for productivity operations."""

from pathlib import Path

from fastmcp import FastMCP

from app.domain.interfaces.performance import IPerformanceService
from app.domain.interfaces.vault import IVaultService
from app.services.productivity import ProductivityService
from app.tools.base import BaseTools


class ProductivityTools(BaseTools):
    def __init__(
        self,
        productivity: ProductivityService,
        vault: IVaultService,
        mcp: FastMCP,
        performance_service: IPerformanceService | None = None,
        agent_name: str = "obsidian-mcp",
        model: str = "unknown",
    ) -> None:
        super().__init__(performance_service, agent_name, model)
        self._productivity = productivity
        self._vault = vault
        mcp.tool()(self._wrap(self.create_daily_note))
        mcp.tool()(self._wrap(self.generate_moc))
        mcp.tool()(self._wrap(self.search_vault))
        mcp.tool()(self._wrap(self.get_note))

    def create_daily_note(self, content: str | None = None) -> str:
        """Create or append to today's daily note."""
        path = self._productivity.create_daily_note(content)
        return f"Daily note: {path}"

    def generate_moc(self, folder: str) -> str:
        """Generate Map of Content for a vault folder."""
        content = self._productivity.generate_moc(folder)
        return f"MOC generated:\n{content}"

    def search_vault(self, query: str) -> str:
        """Full-text search across all vault markdown files."""
        results = self._vault.search_content(query)
        if not results:
            return "No results found."
        lines: list[str] = []
        for path, context in results[:20]:
            lines.append(f"- {path}: {context}")
        return "\n".join(lines)

    def get_note(self, path: str) -> str:
        """Read a note by its path (relative to vault root)."""
        return self._vault.read(self._vault.root / Path(path))
