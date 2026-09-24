from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema.validators import validator_for

from extraction_agent.config.schema import KNOWN_MODALITIES, Profile

DEFAULT_RESOLUTION_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "resolution.schema.json"


@dataclass(frozen=True)
class LoadedProfile:
    profile: Profile
    output_schema: dict
    resolution_schema: dict


def _load_json_schema(path: Path) -> dict:
    schema = json.loads(path.read_text(encoding="utf-8"))
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    return schema


def load_profile(path: str | Path) -> LoadedProfile:
    """Load a profile YAML, validate it, and eagerly load + sanity-check the
    JSON Schema files it references. Schema paths in the YAML are resolved
    relative to the profile file itself, not the process cwd."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    base_dir = path.parent

    if "output_schema_path" in raw:
        raw["output_schema_path"] = base_dir / raw["output_schema_path"]
    if raw.get("resolution_schema_path"):
        raw["resolution_schema_path"] = base_dir / raw["resolution_schema_path"]
    for agent, skill_path in (raw.get("skills") or {}).items():
        raw["skills"][agent] = base_dir / skill_path

    profile = Profile.model_validate(raw)

    unknown = set(profile.modalities) - set(KNOWN_MODALITIES)
    if unknown:
        raise ValueError(f"profile {profile.name!r} references unknown modalities: {sorted(unknown)}")

    output_schema = _load_json_schema(profile.output_schema_path)
    resolution_schema = _load_json_schema(
        profile.resolution_schema_path or DEFAULT_RESOLUTION_SCHEMA_PATH
    )

    return LoadedProfile(profile=profile, output_schema=output_schema, resolution_schema=resolution_schema)
