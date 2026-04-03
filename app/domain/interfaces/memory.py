"""Memory service interface."""

from abc import ABC, abstractmethod

from app.domain.models.conversation_note import ConversationSummary
from app.domain.models.core_note import CoreNote
from app.domain.models.highlight_note import HighlightNote
from app.domain.models.search import SearchResult


class IMemoryService(ABC):
    """Interface for memory read/write operations."""

    @abstractmethod
    def get_core_context(self) -> list[str]:
        """Load all core notes content."""
        ...

    @abstractmethod
    def get_relevant_context(self, query: str, project: str | None = None) -> list[SearchResult]:
        """Return scored results matching query, sorted by relevance."""
        ...

    @abstractmethod
    def save_highlight(self, note: HighlightNote) -> str:
        """Persist a highlight note. Returns the file path."""
        ...

    @abstractmethod
    def save_core(self, note: CoreNote) -> str:
        """Persist a core note. Returns the file path."""
        ...

    @abstractmethod
    def save_conversation(self, note: ConversationSummary) -> str:
        """Persist a conversation summary. Returns the file path."""
        ...

    @abstractmethod
    def rebuild_index(self) -> str:
        """Rebuild MEMORY.md from all files. Returns the index content."""
        ...
