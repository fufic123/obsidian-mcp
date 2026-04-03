"""Entry point — DI wiring and FastMCP initialization."""

import os
import tomllib
from pathlib import Path

from fastmcp import FastMCP

from app.adapters.index import IndexService
from app.adapters.search import FrontmatterSearchService
from app.adapters.vault import FileVaultService
from app.domain.models.config import AppConfig, MemoryConfig, NamespaceConfig
from app.services.memory import MemoryService
from app.services.productivity import ProductivityService
from app.services.tasks import TaskService
from app.tools.memory import register_memory_tools
from app.tools.productivity import register_productivity_tools
from app.tools.tasks import register_task_tools


def _load_config() -> AppConfig:
    """Load configuration from config.toml."""
    config_paths = [
        # 1. Explicit env var
        Path(p) if (p := os.environ.get("OBSIDIAN_MCP_CONFIG")) else None,
        # 2. XDG-style user config
        Path.home() / ".config" / "obsidian-mcp" / "config.toml",
        # 3. Local (for development)
        Path("config.toml"),
    ]
    for config_path in config_paths:
        if config_path is not None and config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            raw_ns = data.get("namespaces", {})
            namespaces = {name: NamespaceConfig(**ns) for name, ns in raw_ns.items()}
            return AppConfig(
                namespaces=namespaces,
                memory=MemoryConfig(**data.get("memory", {})),
            )
    return AppConfig()


def create_app() -> FastMCP:
    """Create and wire up the MCP application."""
    config = _load_config()
    cwd = os.environ.get("PWD", os.getcwd())
    vault_path = config.resolve_vault(cwd)

    # Ensure vault directory exists
    vault_path.mkdir(parents=True, exist_ok=True)

    # Wire up dependencies
    vault = FileVaultService(vault_path)
    search = FrontmatterSearchService(vault, config.memory)
    index = IndexService(vault, config.memory)
    memory = MemoryService(vault, search, index)
    tasks = TaskService(vault)
    productivity = ProductivityService(vault)

    # Create MCP server
    mcp = FastMCP("obsidian-mcp", instructions="Obsidian vault memory server")

    # Register all tools
    register_memory_tools(mcp, memory)
    register_task_tools(mcp, tasks)
    register_productivity_tools(mcp, productivity, vault)

    return mcp


def run() -> None:
    """Run the MCP server via stdio transport."""
    app = create_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    run()
