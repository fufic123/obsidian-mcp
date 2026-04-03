"""Memory service — core business logic for memory operations."""

from app.adapters.index import IndexService
from app.domain.interfaces.memory import IMemoryService
from app.domain.interfaces.search import ISearchService
from app.domain.interfaces.vault import IVaultService
from app.domain.models.conversation_note import ConversationSummary
from app.domain.models.core_note import CoreNote
from app.domain.models.highlight_note import HighlightNote
from app.domain.models.search import SearchQuery, SearchResult


class MemoryService(IMemoryService):
    """File-based memory backed by Obsidian vault."""

    def __init__(
        self,
        vault: IVaultService,
        search: ISearchService,
        index: IndexService,
    ) -> None:
        self._vault = vault
        self._search = search
        self._index = index

    def get_core_context(self) -> list[str]:
        """Load all core notes content."""
        files = self._vault.list_files(self._vault.core_path)
        results: list[str] = []
        for f in files:
            if f.name.startswith("INDEX"):
                continue
            content = self._vault.read(f)
            results.append(content)
        return results

    def get_relevant_context(self, query: str, project: str | None = None) -> list[SearchResult]:
        """Return scored results matching query, sorted by relevance."""
        return self._search.search(SearchQuery(query=query, project=project))

    def save_highlight(self, note: HighlightNote) -> str:
        """Persist a highlight note. Returns the file path."""
        path = self._vault.highlights_path / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        return str(path)

    def save_core(self, note: CoreNote) -> str:
        """Persist a core note. Returns the file path."""
        path = self._vault.core_path / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        return str(path)

    def save_conversation(self, note: ConversationSummary) -> str:
        """Persist a conversation summary. Returns the file path."""
        summary_path = self._vault.conversations_path / "summaries" / f"{note.slug}.md"
        self._vault.write(summary_path, note.to_markdown())
        # Also save full content to archive
        archive_path = self._vault.conversations_path / "archive" / f"{note.slug}.md"
        self._vault.write(archive_path, note.full_content)
        return str(summary_path)

    def rebuild_index(self) -> str:
        """Rebuild MEMORY.md from all files."""
        return self._index.rebuild()
