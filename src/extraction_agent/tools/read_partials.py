from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import StructuredTool


def make_read_all_partials_tool(partials_dir: str | Path) -> StructuredTool:
    """Deterministic filesystem read for the merge agent — every partial
    per-file extraction recorded so far, as {source_modality, source_file,
    fields}. Kept as an explicit tool rather than relying on whatever
    generic file-browsing tools the deepagents backend wiring may or may not
    expose for the /scratch mount, since that surface wasn't verifiable
    against the installed package (see backends.py note)."""

    def _run() -> list[dict]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(partials_dir).glob("*.json"))]

    return StructuredTool.from_function(
        func=_run,
        name="read_all_partials",
        description="Read every partial per-file extraction recorded so far.",
    )
