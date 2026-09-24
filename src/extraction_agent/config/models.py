from __future__ import annotations

from extraction_agent.config.schema import ModelConfig


def resolve_model(cfg: ModelConfig) -> str:
    """deepagents/langchain's `init_chat_model` convention: a "provider:name"
    string. Per-model extra kwargs (temperature, etc.) aren't threaded
    through yet — extend this to return a configured chat model instance
    instead of a string once a profile needs them."""
    return f"{cfg.provider}:{cfg.name}"
