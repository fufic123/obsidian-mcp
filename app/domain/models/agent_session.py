"""AgentSession — groups tool calls from a single agent run."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models.base import extract_frontmatter, render_frontmatter

_TABLE_HEADER = (
    "| tool_name | time | duration_ms | status | tokens_in | tokens_out | cost_usd | error |\n"
    "|-----------|------|-------------|--------|-----------|------------|----------|-------|"
)


class AgentSession(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    agent_name: str
    model: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    status: Literal["active", "completed"] = "active"
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    @classmethod
    def from_content(cls, content: str) -> AgentSession | None:
        """Parse an AgentSession from a session file's frontmatter."""
        fields = extract_frontmatter(content)
        if not fields.get("session_id"):
            return None
        ended_raw = fields.get("ended_at", "")
        return cls(
            session_id=fields["session_id"],
            agent_name=fields.get("agent_name", "unknown"),
            model=fields.get("model", "unknown"),
            started_at=datetime.fromisoformat(fields["started_at"])
            if fields.get("started_at")
            else datetime.now(UTC),
            ended_at=datetime.fromisoformat(ended_raw) if ended_raw else None,
            status=fields.get("status", "active"),  # type: ignore[arg-type]
            total_tool_calls=int(fields.get("total_tool_calls", 0)),
            total_input_tokens=int(fields.get("total_input_tokens", 0)),
            total_output_tokens=int(fields.get("total_output_tokens", 0)),
            total_cost_usd=float(fields.get("total_cost_usd", 0.0)),
        )

    def frontmatter(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "total_tool_calls": self.total_tool_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
        }

    def to_markdown(self) -> str:
        """Render initial session file with frontmatter and empty table."""
        fm = render_frontmatter(self.frontmatter())
        return f"{fm}\n\n{_TABLE_HEADER}\n"

    @property
    def slug(self) -> str:
        return f"{self.started_at.date().isoformat()}-{self.session_id}"

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()
