from __future__ import annotations

from pathlib import Path

from extraction_agent.config.loader import LoadedProfile, load_profile


def load_and_build(profile_path: str | Path) -> LoadedProfile:
    """Load + validate a profile and its schemas once; a caller (CLI, tests,
    a future queue consumer) can reuse the result across many batches.

    Backends and the extraction store are deliberately NOT built here — the
    scratch backend is a per-batch temp dir owned by ExtractionStore
    (see state.py / graph.run_pipeline), so they're created fresh per call
    to run_pipeline rather than shared across batches.
    """
    return load_profile(profile_path)
