from __future__ import annotations

import json
import re
import shutil
import tempfile
import threading
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Callable

from extraction_agent.schemas.resolution import UnresolvedField

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_.-]")


@dataclass
class PartialExtraction:
    source_modality: str
    source_file: str
    fields: dict


class ExtractionStore:
    """Per-run collection of partial per-file results and flagged fields —
    the "extraction store" from the architecture doc.

    Partials are written to per-run temp files rather than kept as an
    in-memory Python list, and rather than a vector DB: the batch is small
    (<10 files) and the merge agent needs *all* of them, not a top-k
    semantic subset, so there's nothing for embeddings/similarity search to
    buy here. Files also give the merge agent a real, inspectable read
    surface (matches the architecture doc's "filesystem read (all
    partials)") instead of everything being pre-flattened into its prompt.

    No durability guarantee across process restarts is intended or needed —
    LangGraph checkpointer-backed state was explicitly ruled out for this
    module. The temp dir only needs to survive one run.
    """

    def __init__(self, scratch_dir: str | Path | None = None) -> None:
        self._lock = threading.Lock()
        self._owns_dir = scratch_dir is None
        self.scratch_dir = Path(scratch_dir) if scratch_dir else Path(tempfile.mkdtemp(prefix="extraction-run-"))
        self.partials_dir = self.scratch_dir / "partials"
        self.partials_dir.mkdir(parents=True, exist_ok=True)
        self._partial_seq = count()
        self._flagged: list[UnresolvedField] = []

    def make_recorder(self, modality: str) -> Callable[[dict], str]:
        """One modality's extraction tool is shared across every file of
        that type in a run, so the file is identified by a `source_file`
        field the tool schema requires (injected in
        modalities.base.make_modality_subagent), not bound at build time."""

        def _on_result(fields: dict) -> str:
            fields = dict(fields)
            source_file = fields.pop("source_file", "unknown")
            payload = {"source_modality": modality, "source_file": source_file, "fields": fields}
            with self._lock:
                n = next(self._partial_seq)
                safe_name = _UNSAFE_CHARS.sub("_", Path(source_file).name) or "file"
                path = self.partials_dir / f"{n:03d}_{modality}_{safe_name}.json"
                path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            return f"recorded partial extraction from {source_file} -> {path.name}"

        return _on_result

    def flag(self, entry: UnresolvedField) -> str:
        with self._lock:
            self._flagged.append(entry)
        return f"flagged {entry.field} ({entry.reason})"

    @property
    def partials(self) -> list[PartialExtraction]:
        """Reads straight from disk each time so this is always consistent
        with what the merge agent's read_all_partials tool would see —
        single source of truth, no separate in-memory copy to drift."""
        results = []
        for path in sorted(self.partials_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(PartialExtraction(**data))
        return results

    @property
    def flagged(self) -> list[UnresolvedField]:
        with self._lock:
            return list(self._flagged)

    def cleanup(self) -> None:
        if self._owns_dir:
            shutil.rmtree(self.scratch_dir, ignore_errors=True)
