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

    def _collect_entries(self, directory: Path) -> list[str]:
        """Collect index entries from a directory (non-recursive)."""
        entries: list[str] = []
        files = self._vault.list_files(directory)
        for file_path in files:
            if file_path.stem.isupper():
                continue
            try:
                content = self._vault.read(file_path)
                lines = content.splitlines()[: self._config.frontmatter_scan_lines]
                fm = _parse_frontmatter(lines)
                name = fm.get("name", file_path.stem)
                description = fm.get("description", "")
                try:
                    rel_path = file_path.relative_to(self._vault.memory_path)
                except ValueError:
                    rel_path = file_path.relative_to(self._vault.root)
                entries.append(f"- [{name}]({rel_path}) \u2014 {description}")
            except Exception:
                continue
        return entries

    def rebuild_highlights(self) -> str:
        """Rebuild highlights/HIGHLIGHTS.md index grouped by project."""
        by_project: dict[str, list[str]] = {}

        for file_path in self._vault.list_files(self._vault.highlights_path, recursive=True):
            if file_path.stem.isupper():
                continue
            try:
                content = self._vault.read(file_path)
                lines_fm = content.splitlines()[: self._config.frontmatter_scan_lines]
                fm = _parse_frontmatter(lines_fm)
                name = str(fm.get("name", file_path.stem))
                description = str(fm.get("description", ""))
                tags_raw = fm.get("tags", [])
                tags = tags_raw if isinstance(tags_raw, list) else []
                project = str(fm.get("project", "") or file_path.parent.name)
                rel_path = file_path.relative_to(self._vault.highlights_path)
                tag_str = f" [{', '.join(str(t) for t in tags)}]" if tags else ""
                by_project.setdefault(project, []).append(
                    f"- [{name}]({rel_path}) \u2014 {description}{tag_str}"
                )
            except Exception:
                continue

        sections: list[str] = ["# Highlights\n"]
        for project in sorted(by_project):
            sections.append(f"## Project: {project}\n")
            sections.extend(by_project[project])
            sections.append("")

        index_content = "\n".join(sections)
        self._vault.write(self._vault.highlights_path / "HIGHLIGHTS.md", index_content)
        return index_content

    def rebuild(self) -> str:
        """Rebuild MEMORY.md from all memory files."""
        sections: list[str] = [
            "# Memory Index\n",
            "## Tasks",
            "- [TASKS.md](../tasks/TASKS.md) — open tasks grouped by project and priority",
            "",
            "## Highlights",
            "- [HIGHLIGHTS.md](highlights/HIGHLIGHTS.md)"
            " \u2014 insights and decisions grouped by project",
            "",
        ]

        # Core section
        core_entries = self._collect_entries(self._vault.core_path)
        if core_entries:
            sections.append("## Core")
            sections.extend(core_entries)
            sections.append("")

        # Conversations section
        summaries_path = self._vault.conversations_path / "summaries"
        conv_entries = self._collect_entries(summaries_path)
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

        index_path = self._vault.memory_path / "MEMORY.md"
        self._vault.write(index_path, content)
        return content
