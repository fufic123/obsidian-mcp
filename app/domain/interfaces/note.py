"""INote — base interface for all vault note types."""

from abc import ABC, abstractmethod


class INote(ABC):
    """Base contract for all vault note types."""

    @abstractmethod
    def to_markdown(self) -> str:
        """Render note as markdown string with frontmatter."""
        ...

    @abstractmethod
    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields as dict."""
        ...

    @property
    @abstractmethod
    def slug(self) -> str:
        """URL-safe filename without extension."""
        ...
