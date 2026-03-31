"""Search service interface."""

from abc import ABC, abstractmethod

from app.domain.models.search import SearchQuery, SearchResult


class ISearchService(ABC):
    """Interface for frontmatter-based search."""

    @abstractmethod
    def search(self, query: SearchQuery) -> list[SearchResult]:
        """Search vault files by frontmatter fields."""
        ...
