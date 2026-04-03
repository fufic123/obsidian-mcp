"""ToolCallRecord — single AI tool call with performance metrics."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    tool_name: str
    agent_name: str
    model: str
    session_id: str
    called_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float
    status: Literal["ok", "error"]
    error: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

    def to_table_row(self) -> str:
        """Render as a markdown table row."""
        time_str = self.called_at.strftime("%H:%M:%S")
        tokens_in = str(self.input_tokens) if self.input_tokens is not None else ""
        tokens_out = str(self.output_tokens) if self.output_tokens is not None else ""
        cost = f"{self.estimated_cost_usd:.6f}" if self.estimated_cost_usd is not None else ""
        error = self.error or ""
        return (
            f"| {self.tool_name} | {time_str} | {self.duration_ms:.1f}"
            f" | {self.status} | {tokens_in} | {tokens_out} | {cost} | {error} |"
        )
