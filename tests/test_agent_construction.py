from pathlib import Path

import pytest

pytest.importorskip("deepagents")

from extraction_agent.agents.merge import build_merge_agent
from extraction_agent.agents.triage import build_triage_agent
from extraction_agent.backends import build_backends
from extraction_agent.factory import load_and_build
from extraction_agent.state import ExtractionStore

PROFILE_PATH = Path(__file__).parent.parent / "profiles" / "invoice-intake.yaml"


@pytest.fixture
def loaded():
    return load_and_build(PROFILE_PATH)


def test_triage_agent_builds_with_all_modality_subagents(loaded):
    """Construction only — no LLM call. Exercises the real CompositeBackend
    wiring, SubAgent specs (system_prompt/skills/model keys), and the
    JSON-Schema-derived extraction tools against the actual deepagents API,
    not our own guesses about it."""
    store = ExtractionStore()
    try:
        backends = build_backends(store.scratch_dir)
        agent = build_triage_agent(loaded, backends=backends, extraction_store=store)
        assert agent is not None
    finally:
        store.cleanup()


def test_merge_agent_builds(loaded):
    store = ExtractionStore()
    try:
        backends = build_backends(store.scratch_dir)
        agent = build_merge_agent(loaded, backends=backends, extraction_store=store, result_holder={})
        assert agent is not None
    finally:
        store.cleanup()
