"""Search-related models."""

from pathlib import Path

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Parameters for a vault search."""

    query: str
    project: str | None = None


class SearchResult(BaseModel):
    """A single search result with relevance score."""

    path: Path
    name: str
    description: str
    score: float
    note_type: str
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
