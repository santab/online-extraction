from __future__ import annotations

from typing import Any

from deepagents import create_deep_agent

from extraction_agent.backends import PipelineBackends, skills_deny_write_permission, to_virtual_skill_path
from extraction_agent.config.loader import LoadedProfile
from extraction_agent.config.models import resolve_model
from extraction_agent.state import ExtractionStore
from extraction_agent.tools.extraction_tool import make_extraction_tool
from extraction_agent.tools.flag_field import make_flag_field_tool
from extraction_agent.tools.read_partials import make_read_all_partials_tool

_SYSTEM_PROMPT = """\
You reconcile partial per-file extraction results into the single final
output. Sources may disagree, or a field may be missing everywhere.

Start by calling read_all_partials to see every source's extracted fields —
don't guess at what was extracted.

For every field in the output schema:
- If sources agree (or only one source has it), use that value.
- If sources conflict and you can't confidently pick one, still choose your
  best-available value AND call flag_field with the field name, the
  candidate values, their sources, and reason="conflicting".
- If no source has the field, leave it unset and call flag_field with
  reason="missing".
- If you have a value but low confidence in it, call flag_field with
  reason="low_confidence" in addition to including the value.

Call flag_field as a plain data-recording step — it does not pause you or
require a response back. Finish by calling the final extraction tool exactly
once with your best-available values for every field you could fill.

A "merge" skill is available with source-of-truth/conflict-resolution
rules — check it before reconciling.
"""


def build_merge_agent(
    loaded: LoadedProfile,
    *,
    backends: PipelineBackends,
    extraction_store: ExtractionStore,
    result_holder: dict[str, Any],
):
    """`result_holder` is mutated in place by the final extraction tool —
    the caller reads result_holder["output"] after invoking the agent."""
    profile = loaded.profile

    def _on_final_result(fields: dict) -> str:
        result_holder["output"] = fields
        return "recorded final merged output"

    final_tool = make_extraction_tool(
        name="emit_final_output",
        description="Record the fully reconciled output for the whole batch.",
        schema=loaded.output_schema,
        on_result=_on_final_result,
    )
    flag_tool = make_flag_field_tool(on_flag=extraction_store.flag)
    read_partials_tool = make_read_all_partials_tool(extraction_store.partials_dir)

    return create_deep_agent(
        model=resolve_model(profile.model_for("merge")),
        tools=[read_partials_tool, final_tool, flag_tool],
        system_prompt=_SYSTEM_PROMPT,
        skills=[to_virtual_skill_path(profile.skill_path_for("merge"))],
        permissions=[skills_deny_write_permission()],
        backend=backends.composite,
    )


def run_merge(agent, *, repair_note: str = "") -> None:
    message = repair_note or "Reconcile the recorded partial extractions into the final output."
    agent.invoke({"messages": [{"role": "user", "content": message}]})
