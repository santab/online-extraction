from __future__ import annotations

from typing import Any, Callable, Protocol

from extraction_agent.backends import PipelineBackends
from extraction_agent.config.models import resolve_model
from extraction_agent.config.schema import ModelConfig
from extraction_agent.tools.extraction_tool import make_extraction_tool

_SYSTEM_PROMPT_TEMPLATE = """\
You extract fields from a single {name} file using the tools provided.

1. Call the parser tool to read the file's content.
2. Call emit_{name}_partial_extraction exactly once with every field this
   file supports, including `source_file` set to the exact file path you
   were given. Leave fields this file doesn't cover unset — the merge step
   reconciles across sources, you don't need to guess.

A "{name}" skill is available with format-specific gotchas for this file
type — check it before extracting.
"""


class Modality(Protocol):
    """One plugin per file type (pdf/excel/image/docx) — the extensibility
    seam called out in the architecture doc. A modality contributes a
    deepagents SubAgent spec that triage can delegate to via the `task`
    tool; the sub-agent's own tools do the deterministic parsing + forced
    schema-extraction call."""

    name: str

    def build_subagent(
        self,
        *,
        model: ModelConfig,
        output_schema: dict,
        backends: PipelineBackends,
        skill_source: str,
        on_partial_result: Callable[[dict[str, Any]], str],
    ) -> dict:
        """Return a deepagents SubAgent spec dict: {name, description,
        system_prompt, tools, model, skills}. `skill_source` is the virtual
        `/skills/<agent>/vN/` path this subagent's `skills=[...]` should
        reference (see backends.to_virtual_skill_path). `on_partial_result`
        is called by the sub-agent's extraction tool to write into the
        extraction store."""
        ...


def make_modality_subagent(
    *,
    name: str,
    description: str,
    parser_tool: Any,
    model: ModelConfig,
    output_schema: dict,
    skill_source: str,
    on_partial_result: Callable[[dict[str, Any]], str],
    extra_tools: list[Any] | None = None,
) -> dict:
    """Shared SubAgent-spec builder used by every modality: a parser tool to
    read the file's raw content into context, plus the forced partial-schema
    extraction tool the sub-agent must call to "answer". Modalities differ
    only in `parser_tool` (and occasionally `extra_tools`, e.g. the image
    sub-agent's VLM call).

    One modality's extraction tool is reused across every file of that type
    triage delegates in a run, so `source_file` is injected into the schema
    as a required field — otherwise a partial result can't be attributed
    back to the file it came from. See ExtractionStore.make_recorder."""
    partial_schema = {
        **output_schema,
        "properties": {
            "source_file": {"type": "string", "description": "Path of the file this data was extracted from."},
            **output_schema.get("properties", {}),
        },
        "required": ["source_file", *output_schema.get("required", [])],
    }
    extraction_tool = make_extraction_tool(
        name=f"emit_{name}_partial_extraction",
        description=(
            "Record this file's extracted fields against the output schema. "
            "Fill only what this single file supports; leave the rest unset "
            "for the merge step to reconcile across sources."
        ),
        schema=partial_schema,
        on_result=on_partial_result,
    )
    return {
        "name": name,
        "description": description,
        "system_prompt": _SYSTEM_PROMPT_TEMPLATE.format(name=name),
        "tools": [parser_tool, extraction_tool, *(extra_tools or [])],
        "model": resolve_model(model),
        "skills": [skill_source],
    }
