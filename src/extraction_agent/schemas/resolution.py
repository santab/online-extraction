from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

Reason = Literal["missing", "conflicting", "low_confidence"]


class UnresolvedField(BaseModel):
    """One entry written by the merge agent's flag_field tool. Mirrors
    resolution.schema.json — kept as a typed helper for building the
    resolution.json payload, not as the schema of record."""

    field: str
    candidates: list[Any] = []
    sources: list[str] = []
    reason: Reason


def build_resolution_payload(fields: list[UnresolvedField]) -> dict:
    return {"unresolved_fields": [f.model_dump() for f in fields]}
