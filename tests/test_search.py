"""Tests for FrontmatterSearchService."""

from app.adapters.search import FrontmatterSearchService, _parse_frontmatter, _score_match
from app.adapters.vault import FileVaultService
from app.domain.models.search import SearchQuery


def test_parse_frontmatter() -> None:
    """Parse valid frontmatter."""
    lines = [
        "---",
        "name: Test Note",
        "description: A test",
        "type: highlight",
        "tags: [python, mcp]",
        "---",
    ]
    fm = _parse_frontmatter(lines)
    assert fm["name"] == "Test Note"
    assert fm["tags"] == ["python", "mcp"]


def test_parse_frontmatter_empty() -> None:
    """Return empty dict for no frontmatter."""
    assert _parse_frontmatter([]) == {}
    assert _parse_frontmatter(["no frontmatter"]) == {}


def test_score_match() -> None:
    """Score based on field matches."""
    fm: dict[str, str | list[str]] = {
        "name": "Python MCP server",
        "description": "Building an MCP server",
        "tags": ["python", "mcp"],
    }
    score = _score_match("python", fm)
    assert score > 0
    # Name match (3.0) + description doesn't contain "python" + tag match (1.5)
    assert score == 4.5


def test_search_finds_highlights(search: FrontmatterSearchService, vault: FileVaultService) -> None:
    """Search returns matching highlights."""
    content = (
        "---\n"
        "name: Python Tips\n"
        "description: Useful Python tricks\n"
        "type: highlight\n"
        "tags: [python]\n"
        "created: 2026-01-01\n"
        "---\n\n"
        "Some content here.\n"
    )
    vault.write(vault.highlights_path / "python-tips.md", content)

    results = search.search(SearchQuery(query="python"))
    assert len(results) == 1
    assert results[0].name == "Python Tips"


def test_search_filters_by_project(
    search: FrontmatterSearchService, vault: FileVaultService
) -> None:
    """Search respects project filter."""
    for name, project in [("a", "work"), ("b", "personal")]:
        content = (
            f"---\nname: Note {name}\ndescription: desc\n"
            f"type: highlight\nproject: {project}\ntags: [code]\n---\n"
        )
        vault.write(vault.highlights_path / f"{name}.md", content)

    results = search.search(SearchQuery(query="code", project="work"))
    assert len(results) == 1
    assert results[0].project == "work"
