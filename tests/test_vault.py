"""Tests for FileVaultService."""

from pathlib import Path

import pytest

from app.adapters.vault import FileVaultService
from app.domain.exceptions.vault import (
    PathSecurityError,
    VaultNotFoundError,
    VaultReadError,
)


def test_vault_not_found(tmp_path: Path) -> None:
    """Raise VaultNotFoundError for non-existent path."""
    with pytest.raises(VaultNotFoundError):
        FileVaultService(tmp_path / "nonexistent")


def test_read_write(vault: FileVaultService, vault_root: Path) -> None:
    """Write and read back a file."""
    path = vault_root / "test.md"
    vault.write(path, "hello world")
    assert vault.read(path) == "hello world"


def test_read_missing_file(vault: FileVaultService, vault_root: Path) -> None:
    """Raise VaultReadError for missing file."""
    with pytest.raises(VaultReadError):
        vault.read(vault_root / "missing.md")


def test_path_traversal_blocked(vault: FileVaultService, vault_root: Path) -> None:
    """Block path traversal attempts."""
    with pytest.raises(PathSecurityError):
        vault.read(vault_root / ".." / "etc" / "passwd")


def test_list_files(vault: FileVaultService, vault_root: Path) -> None:
    """List markdown files in a directory."""
    (vault_root / "memory" / "core" / "a.md").write_text("a")
    (vault_root / "memory" / "core" / "b.md").write_text("b")
    (vault_root / "memory" / "core" / "c.txt").write_text("c")
    files = vault.list_files(vault_root / "memory" / "core")
    assert len(files) == 2
    assert all(f.suffix == ".md" for f in files)


def test_exists(vault: FileVaultService, vault_root: Path) -> None:
    """Check file existence."""
    path = vault_root / "test.md"
    assert not vault.exists(path)
    path.write_text("x")
    assert vault.exists(path)


def test_search_content(vault: FileVaultService, vault_root: Path) -> None:
    """Full-text search finds matching files."""
    (vault_root / "a.md").write_text("Python is great")
    (vault_root / "b.md").write_text("JavaScript too")
    results = vault.search_content("python")
    assert len(results) == 1
    assert "Python is great" in results[0][1]


def test_write_creates_directories(vault: FileVaultService, vault_root: Path) -> None:
    """Write creates parent directories automatically."""
    path = vault_root / "new" / "nested" / "file.md"
    vault.write(path, "content")
    assert vault.read(path) == "content"
