from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

KNOWN_AGENTS = ("triage", "merge", "pdf", "excel", "image", "docx")
KNOWN_MODALITIES = ("pdf", "excel", "image", "docx")


class ModelConfig(BaseModel):
    """Per-agent model selection. Kept provider-agnostic so a profile can mix
    e.g. a cheap model for modality sub-agents and a stronger one for merge."""

    provider: str
    name: str
    kwargs: dict = Field(default_factory=dict)


class Profile(BaseModel):
    name: str
    modalities: list[str]
    output_schema_path: Path
    resolution_schema_path: Path | None = None
    models: dict[str, ModelConfig]
    # Each path is a skills/<agent>/vN/ *directory* (deepagents' skills=
    # sources are scanned for immediate subdirectories containing a
    # SKILL.md, so this must be the version dir, not the SKILL.md file
    # itself). Pointing at a specific vN pins exactly which revision this
    # profile uses so editing a skill for one profile/tenant can't silently
    # regress another profile still pointing at an older vN.
    skills: dict[str, Path] = Field(default_factory=dict)
    confidence_threshold: float = 0.7
    max_repair_turns: int = 1

    def model_for(self, agent: str) -> ModelConfig:
        try:
            return self.models[agent]
        except KeyError:
            raise ValueError(
                f"profile {self.name!r} has no model configured for agent {agent!r}"
            ) from None

    def skill_path_for(self, agent: str) -> Path | None:
        return self.skills.get(agent)
