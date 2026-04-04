"""Frontmatter-based search service implementation."""

from pathlib import Path

from app.domain.interfaces.search import ISearchService
from app.domain.interfaces.vault import IVaultService
from app.domain.models.config import MemoryConfig
from app.domain.models.search import SearchQuery, SearchResult


def _parse_frontmatter(lines: list[str]) -> dict[str, str | list[str]]:
    """Parse YAML frontmatter from first N lines of a file."""
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str | list[str]] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        value = value.strip()
        # Parse simple list format: [tag1, tag2]
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            fields[key.strip()] = items
        else:
            fields[key.strip()] = value
    return fields


def _score_match(query: str, fm: dict[str, str | list[str]]) -> float:
    """Score frontmatter fields against query terms."""
    query_terms = query.lower().split()
    if not query_terms:
        return 0.0

    score = 0.0
    name = str(fm.get("name", "")).lower()
    description = str(fm.get("description", "")).lower()
    tags_raw = fm.get("tags", [])
    tags = [t.lower() for t in tags_raw] if isinstance(tags_raw, list) else []

    for term in query_terms:
        if term in name:
            score += 3.0
        if term in description:
            score += 2.0
        if any(term in tag for tag in tags):
            score += 1.5

    return score


class FrontmatterSearchService(ISearchService):
    """Search vault files by scanning frontmatter."""

    def __init__(self, vault: IVaultService, config: MemoryConfig) -> None:
        self._vault = vault
        self._config = config

    def _scan_directory(
        self, directory: Path, recursive: bool = False
    ) -> list[tuple[Path, dict[str, str | list[str]]]]:
        """Scan frontmatter of all markdown files in a directory."""
        results: list[tuple[Path, dict[str, str | list[str]]]] = []
        files = self._vault.list_files(directory, recursive=recursive)
        for file_path in files:
            if file_path.stem.isupper():
                continue
            try:
                content = self._vault.read(file_path)
                lines = content.splitlines()[: self._config.frontmatter_scan_lines]
                fm = _parse_frontmatter(lines)
                if fm:
                    results.append((file_path, fm))
            except Exception:
                continue
        return results

    def search(self, query: SearchQuery) -> list[SearchResult]:
        """Search vault files by frontmatter fields."""
        all_entries: list[tuple[Path, dict[str, str | list[str]]]] = []

        # Scan highlights (recursive — files live in project subfolders) and conversation summaries
        all_entries.extend(self._scan_directory(self._vault.highlights_path, recursive=True))
        summaries_path = self._vault.conversations_path / "summaries"
        all_entries.extend(self._scan_directory(summaries_path))

        results: list[SearchResult] = []
        for path, fm in all_entries:
            # Filter by project if specified
            if query.project:
                fm_project = str(fm.get("project", ""))
                if fm_project != query.project:
                    continue

            score = _score_match(query.query, fm)
            if score <= 0:
                continue

            # Boost by mtime for recency
            try:
                mtime = path.stat().st_mtime
                score += mtime / 1e12  # Small recency bonus
            except OSError:
                pass

            tags_raw = fm.get("tags", [])
            tags = tags_raw if isinstance(tags_raw, list) else []

            results.append(
                SearchResult(
                    path=path,
                    name=str(fm.get("name", path.stem)),
                    description=str(fm.get("description", "")),
                    score=score,
                    note_type=str(fm.get("type", "unknown")),
                    tags=[str(t) for t in tags],
                    project=str(fm.get("project", "")) or None,
                )
            )

        # Sort: score DESC, then by path for stability
        results.sort(key=lambda r: (-r.score, str(r.path)))
        return results[: self._config.max_search_results]
