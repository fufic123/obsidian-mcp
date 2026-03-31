"""MCP tool wrappers for productivity operations."""

from fastmcp import FastMCP

from app.domain.interfaces.vault import IVaultService
from app.services.productivity import ProductivityService


def register_productivity_tools(
    mcp: FastMCP, productivity: ProductivityService, vault: IVaultService
) -> None:
    """Register productivity-related MCP tools."""

    @mcp.tool()
    def create_daily_note(content: str | None = None) -> str:
        """Create or append to today's daily note."""
        path = productivity.create_daily_note(content)
        return f"Daily note: {path}"

    @mcp.tool()
    def generate_moc(folder: str) -> str:
        """Generate Map of Content for a vault folder."""
        content = productivity.generate_moc(folder)
        return f"MOC generated:\n{content}"

    @mcp.tool()
    def search_vault(query: str) -> str:
        """Full-text search across all vault markdown files."""
        results = vault.search_content(query)
        if not results:
            return "No results found."
        lines: list[str] = []
        for path, context in results[:20]:
            lines.append(f"- {path}: {context}")
        return "\n".join(lines)

    @mcp.tool()
    def get_note(path: str) -> str:
        """Read a note by its path (relative to vault root)."""
        from pathlib import Path

        full_path = vault.root / Path(path)
        return vault.read(full_path)
