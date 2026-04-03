"""Vault service interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class IVaultService(ABC):
    """Interface for vault file operations."""

    @abstractmethod
    def read(self, path: Path) -> str:
        """Read file content from vault."""
        ...

    @abstractmethod
    def write(self, path: Path, content: str) -> None:
        """Write content to a vault file, creating directories as needed."""
        ...

    @abstractmethod
    def list_files(
        self, directory: Path, pattern: str = "*.md", recursive: bool = False
    ) -> list[Path]:
        """List files matching pattern in a vault directory."""
        ...

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if a path exists in the vault."""
        ...

    @property
    @abstractmethod
    def root(self) -> Path:
        """Vault root directory."""
        ...

    @property
    @abstractmethod
    def memory_path(self) -> Path:
        """Path to memory/ directory."""
        ...

    @property
    @abstractmethod
    def highlights_path(self) -> Path:
        """Path to memory/highlights/ directory."""
        ...

    @property
    @abstractmethod
    def core_path(self) -> Path:
        """Path to memory/core/ directory."""
        ...

    @property
    @abstractmethod
    def conversations_path(self) -> Path:
        """Path to memory/conversations/ directory."""
        ...

    @property
    @abstractmethod
    def tasks_path(self) -> Path:
        """Path to tasks/ directory."""
        ...

    @property
    @abstractmethod
    def daily_path(self) -> Path:
        """Path to daily/ directory."""
        ...

    @abstractmethod
    def move(self, src: Path, dst: Path) -> None:
        """Move a file within the vault, creating destination directories as needed."""
        ...

    @abstractmethod
    def search_content(self, query: str) -> list[tuple[Path, str]]:
        """Full-text search across all vault markdown files."""
        ...
