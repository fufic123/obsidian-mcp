"""MEMORY.md index generation service."""

from pathlib import Path

from app.domain.interfaces.vault import IVaultService
from app.domain.models.config import MemoryConfig

from .search import _parse_frontmatter


class IndexService:
    """Generates and manages MEMORY.md index file."""

    def __init__(self, vault: IVaultService, config: MemoryConfig) -> None:
        self._vault = vault
        self._config = config

    def _collect_entries(self, directory: Path, section: str) -> list[str]:
        """Collect index entries from a directory."""
        entries: list[str] = []
        files = self._vault.list_files(directory)
        for file_path in files:
            if file_path.name.startswith("INDEX") or file_path.name == "MEMORY.md":
                continue
            try:
                content = self._vault.read(file_path)
                lines = content.splitlines()[: self._config.frontmatter_scan_lines]
                fm = _parse_frontmatter(lines)
                name = fm.get("name", file_path.stem)
                description = fm.get("description", "")
                # Build relative path from memory/ directory
                try:
                    rel_path = file_path.relative_to(self._vault.memory_path)
                except ValueError:
                    rel_path = file_path.relative_to(self._vault.root)
                entries.append(f"- [{name}]({rel_path}) \u2014 {description}")
            except Exception:
                continue
        return entries

    def rebuild(self) -> str:
        """Rebuild MEMORY.md from all memory files."""
        sections: list[str] = [
            "# Memory Index\n",
            "## Tasks",
            "- [TASKS.md](../tasks/TASKS.md) — open tasks grouped by project and priority",
            "",
        ]

        # Core section
        core_entries = self._collect_entries(self._vault.core_path, "Core")
        if core_entries:
            sections.append("## Core")
            sections.extend(core_entries)
            sections.append("")

        # Highlights section
        highlight_entries = self._collect_entries(self._vault.highlights_path, "Highlights")
        if highlight_entries:
            sections.append("## Highlights")
            sections.extend(highlight_entries)
            sections.append("")

        # Conversations section
        summaries_path = self._vault.conversations_path / "summaries"
        conv_entries = self._collect_entries(summaries_path, "Conversations")
        if conv_entries:
            sections.append("## Conversations")
            sections.extend(conv_entries)
            sections.append("")

        content = "\n".join(sections)

        # Dual truncation: lines first, then bytes
        lines = content.splitlines()
        if len(lines) > self._config.max_index_lines:
            lines = lines[: self._config.max_index_lines]
            content = "\n".join(lines)

        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self._config.max_index_bytes:
            content = content_bytes[: self._config.max_index_bytes].decode("utf-8", errors="ignore")

        # Write to vault
        index_path = self._vault.memory_path / "MEMORY.md"
        self._vault.write(index_path, content)
        return content
