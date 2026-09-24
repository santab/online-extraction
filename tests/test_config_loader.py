from pathlib import Path

import pytest

from extraction_agent.config.loader import load_profile

PROFILE_PATH = Path(__file__).parent.parent / "profiles" / "invoice-intake.yaml"


def test_loads_example_profile():
    loaded = load_profile(PROFILE_PATH)
    assert loaded.profile.name == "invoice-intake"
    assert set(loaded.profile.modalities) == {"pdf", "excel", "image", "docx"}


def test_output_schema_loaded_and_valid():
    loaded = load_profile(PROFILE_PATH)
    assert loaded.output_schema["title"] == "invoice-intake-output"
    assert "invoice_number" in loaded.output_schema["properties"]


def test_resolution_schema_falls_back_to_default():
    loaded = load_profile(PROFILE_PATH)
    assert "unresolved_fields" in loaded.resolution_schema["properties"]


def test_skill_paths_resolved_relative_to_profile_file():
    loaded = load_profile(PROFILE_PATH)
    triage_skill = loaded.profile.skill_path_for("triage")
    assert triage_skill.is_absolute()
    assert triage_skill.exists()


def test_unknown_modality_rejected(tmp_path):
    bad_profile = tmp_path / "bad.yaml"
    bad_profile.write_text(
        """
name: bad
modalities: [pdf, carrier_pigeon]
output_schema_path: schema.json
models:
  triage: {provider: anthropic, name: claude-sonnet-5}
  merge: {provider: anthropic, name: claude-sonnet-5}
  pdf: {provider: anthropic, name: claude-sonnet-5}
"""
    )
    (tmp_path / "schema.json").write_text('{"type": "object", "properties": {}}')

    with pytest.raises(ValueError, match="unknown modalities"):
        load_profile(bad_profile)
