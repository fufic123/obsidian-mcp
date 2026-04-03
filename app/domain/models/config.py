"""Configuration models."""

from pathlib import Path

from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Memory subsystem configuration."""

    max_index_lines: int = 200
    max_index_bytes: int = 25600
    frontmatter_scan_lines: int = 30
    max_search_results: int = 20


class NamespaceConfig(BaseModel):
    """Single namespace entry — named vault with optional cwd matcher."""

    vault: str
    match: str | None = None  # cwd prefix to match; None means default

    def matches(self, cwd: str) -> bool:
        """Return True if this namespace matches the given working directory."""
        if self.match is None:
            return False
        return cwd.startswith(self.match)

    def vault_path(self) -> Path:
        """Resolve vault path, expanding ~ if needed."""
        return Path(self.vault).expanduser()


class AppConfig(BaseModel):
    """Top-level application configuration."""

    namespaces: dict[str, NamespaceConfig] = Field(
        default_factory=lambda: {"default": NamespaceConfig(vault="~/vaults/personal")}
    )
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    def resolve_vault(self, cwd: str) -> Path:
        """Resolve vault path from current working directory.

        Iterates namespaces in definition order; first match wins.
        Falls back to the 'default' namespace if nothing matches.
        """
        for name, ns in self.namespaces.items():
            if name == "default":
                continue
            if ns.matches(cwd):
                return ns.vault_path()

        default = self.namespaces.get("default")
        if default:
            return default.vault_path()

        raise ValueError(f"No vault mapping for cwd={cwd!r}")
