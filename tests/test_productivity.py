"""Tests for ProductivityService."""

from datetime import date

from app.adapters.vault import FileVaultService
from app.services.productivity import ProductivityService


def test_create_daily_note(productivity: ProductivityService, vault: FileVaultService) -> None:
    """Create a daily note for today."""
    path = productivity.create_daily_note("Today I learned about MCP")
    today = date.today().isoformat()
    assert today in path
    assert vault.exists(vault.daily_path / f"{today}.md")


def test_create_daily_note_append(
    productivity: ProductivityService, vault: FileVaultService
) -> None:
    """Append to existing daily note."""
    productivity.create_daily_note("First entry")
    productivity.create_daily_note("Second entry")
    today = date.today().isoformat()
    content = vault.read(vault.daily_path / f"{today}.md")
    assert "First entry" in content
    assert "Second entry" in content


def test_generate_moc(productivity: ProductivityService, vault: FileVaultService) -> None:
    """Generate Map of Content for a folder."""
    vault.write(vault.root / "docs" / "a.md", "# Doc A")
    vault.write(vault.root / "docs" / "b.md", "# Doc B")

    content = productivity.generate_moc("docs")
    assert "Map of Content" in content
    assert "A" in content
    assert "B" in content
