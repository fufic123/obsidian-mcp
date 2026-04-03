"""Base class for all MCP tool groups — provides optional performance tracking."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.domain.interfaces.performance import IPerformanceService

F = TypeVar("F", bound=Callable[..., Any])


class BaseTools:
    """Wraps tool methods with optional performance tracking."""

    def __init__(
        self,
        performance_service: IPerformanceService | None = None,
        session_id: str | None = None,
    ) -> None:
        self.__performance_service = performance_service
        self.__session_id = session_id

    def _wrap(self, fn: F) -> F:
        """Return fn wrapped with timing and performance recording if tracking is enabled."""
        if self.__performance_service is None or self.__session_id is None:
            return fn

        performance_service = self.__performance_service
        session_id = self.__session_id

        @functools.wraps(fn)
        def tracked(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                performance_service.record_tool_call(
                    session_id=session_id,
                    tool_name=fn.__name__,
                    duration_ms=duration_ms,
                    status="ok",
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                performance_service.record_tool_call(
                    session_id=session_id,
                    tool_name=fn.__name__,
                    duration_ms=duration_ms,
                    status="error",
                    error=str(exc),
                )
                raise

        return tracked  # type: ignore[return-value]
