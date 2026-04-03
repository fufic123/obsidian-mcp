"""MCP tool wrappers for performance tracking — exposes session API to external agents."""

from typing import Literal

from fastmcp import FastMCP

from app.domain.interfaces.performance import IPerformanceService


class PerformanceTools:
    def __init__(self, performance_service: IPerformanceService, mcp: FastMCP) -> None:
        self._performance_service = performance_service
        mcp.tool()(self.start_performance_session)
        mcp.tool()(self.record_performance_tool_call)
        mcp.tool()(self.end_performance_session)
        mcp.tool()(self.get_performance_stats)
        mcp.tool()(self.get_performance_dashboard)

    def start_performance_session(self, agent_name: str, model: str) -> str:
        """Start a new tracking session for an agent run. Returns session_id.

        agent_name: identifier for your agent, e.g. 'my-research-agent'.
        model: LLM model ID, e.g. 'claude-sonnet-4-6' or 'gpt-4o'.
        """
        session_id = self._performance_service.start_session(agent_name, model)
        return f"Session started: {session_id}"

    def record_performance_tool_call(
        self,
        session_id: str,
        tool_name: str,
        duration_ms: float,
        status: Literal["ok", "error"],
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        error: str | None = None,
    ) -> str:
        """Record a single tool call into an active session.

        session_id: returned by start_performance_session.
        duration_ms: wall-clock time of the call in milliseconds.
        status: 'ok' or 'error'.
        input_tokens / output_tokens: pass when available for cost estimation.
        """
        self._performance_service.record_tool_call(
            session_id=session_id,
            tool_name=tool_name,
            duration_ms=duration_ms,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error=error,
        )
        return "Recorded."

    def end_performance_session(self, session_id: str) -> str:
        """Mark a session as completed. Call at the end of your agent run."""
        self._performance_service.end_session(session_id)
        return f"Session completed: {session_id}"

    def get_performance_stats(self, agent_name: str | None = None, days: int = 7) -> str:
        """Return aggregated stats: sessions, calls, tokens, cost.

        agent_name: filter to a specific agent, or omit for all agents.
        days: lookback window (default 7).
        """
        return self._performance_service.get_stats(agent_name=agent_name, days=days)

    def get_performance_dashboard(self) -> str:
        """Return a full dashboard grouped by agent for the last 30 days."""
        return self._performance_service.get_dashboard()
