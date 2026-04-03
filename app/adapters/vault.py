"""File-based vault service implementation."""

from pathlib import Path

from app.domain.exceptions.vault import (
    PathSecurityError,
    VaultNotFoundError,
    VaultReadError,
    VaultWriteError,
)
from app.domain.interfaces.vault import IVaultService


class FileVaultService(IVaultService):
    """Vault backed by local filesystem."""

    def __init__(self, vault_root: Path) -> None:
        self._root = vault_root.resolve()
        if not self._root.is_dir():
            raise VaultNotFoundError(f"Vault not found: {self._root}")

    def _validate_path(self, path: Path) -> Path:
        """Validate path is within vault root (double-pass: string + resolve)."""
        # String-level check
        try:
            str_path = str(path)
            if ".." in str_path:
                raise PathSecurityError(f"Path traversal detected: {path}")
        except (TypeError, ValueError) as e:
            raise PathSecurityError(f"Invalid path: {path}") from e

        # Symlink-aware resolve check
        resolved = path.resolve()
        if not str(resolved).startswith(str(self._root)):
            raise PathSecurityError(f"Path escapes vault: {path}")
        return resolved

    def read(self, path: Path) -> str:
        """Read file content from vault."""
        validated = self._validate_path(path)
        try:
            return validated.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise VaultReadError(f"File not found: {path}") from e
        except OSError as e:
            raise VaultReadError(f"Cannot read: {path}") from e

    def write(self, path: Path, content: str) -> None:
        """Write content to a vault file, creating directories as needed."""
        validated = self._validate_path(path)
        try:
            validated.parent.mkdir(parents=True, exist_ok=True)
            validated.write_text(content, encoding="utf-8")
        except OSError as e:
            raise VaultWriteError(f"Cannot write: {path}") from e

    def list_files(self, directory: Path, pattern: str = "*.md", recursive: bool = False) -> list[Path]:
        """List files matching pattern in a vault directory."""
        validated = self._validate_path(directory)
        if not validated.is_dir():
            return []
        glob_fn = validated.rglob if recursive else validated.glob
        return sorted(glob_fn(pattern))

    def exists(self, path: Path) -> bool:
        """Check if a path exists in the vault."""
        try:
            validated = self._validate_path(path)
            return validated.exists()
        except PathSecurityError:
            return False

    @property
    def root(self) -> Path:
        """Vault root directory."""
        return self._root

    @property
    def memory_path(self) -> Path:
        """Path to memory/ directory."""
        return self._root / "memory"

    @property
    def highlights_path(self) -> Path:
        """Path to memory/highlights/ directory."""
        return self._root / "memory" / "highlights"

    @property
    def core_path(self) -> Path:
        """Path to memory/core/ directory."""
        return self._root / "memory" / "core"

    @property
    def conversations_path(self) -> Path:
        """Path to memory/conversations/ directory."""
        return self._root / "memory" / "conversations"

    @property
    def tasks_path(self) -> Path:
        """Path to tasks/ directory."""
        return self._root / "tasks"

    @property
    def daily_path(self) -> Path:
        """Path to daily/ directory."""
        return self._root / "daily"

    def search_content(self, query: str) -> list[tuple[Path, str]]:
        """Full-text search across all vault markdown files."""
        results: list[tuple[Path, str]] = []
        query_lower = query.lower()
        for md_file in self._root.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # Return first matching line as context
                    for line in content.splitlines():
                        if query_lower in line.lower():
                            results.append((md_file, line.strip()))
                            break
            except OSError:
                continue
        return results
