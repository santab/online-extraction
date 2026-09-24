from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import StructuredTool

from extraction_agent.schemas.resolution import UnresolvedField


def make_flag_field_tool(on_flag: Callable[[UnresolvedField], str]) -> StructuredTool:
    """The merge agent calls this when it can't confidently resolve a field
    across sources. This is a plain data-recording call, not an interrupt:
    the pipeline keeps running and the field shows up in resolution.json for
    the external human-in-the-loop system to pick up later."""

    def _run(
        field: str,
        reason: str,
        candidates: list[Any] | None = None,
        sources: list[str] | None = None,
    ) -> str:
        entry = UnresolvedField(
            field=field,
            reason=reason,  # type: ignore[arg-type]
            candidates=candidates or [],
            sources=sources or [],
        )
        return on_flag(entry)

    return StructuredTool.from_function(
        func=_run,
        name="flag_field",
        description=(
            "Record a field that could not be confidently resolved (missing, "
            "conflicting across sources, or low-confidence). Does not pause "
            "the pipeline."
        ),
    )
