from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from extraction_agent.agents.merge import build_merge_agent, run_merge
from extraction_agent.agents.triage import build_triage_agent
from extraction_agent.agents.validate import ValidationResult, validate_and_repair
from extraction_agent.backends import build_backends
from extraction_agent.config.loader import LoadedProfile
from extraction_agent.schemas.resolution import build_resolution_payload
from extraction_agent.state import ExtractionStore

# NOTE: this is plain Python orchestration, not a nested langgraph.StateGraph
# wrapping the triage/merge deep agents. Confirmed with the user that
# durable/LangGraph-checkpointer-backed state management is not required for
# this module — there's no branching or interrupt inside a run either
# (interrupt_on is explicitly unused per the architecture doc's "no
# human-in-the-loop inside this module" boundary) — so a StateGraph here
# would add indirection without buying anything.


@dataclass
class PipelineResult:
    structured_output: dict
    resolution: dict
    validation: ValidationResult


def run_pipeline(loaded: LoadedProfile, file_paths: list[str]) -> PipelineResult:
    extraction_store = ExtractionStore()
    try:
        backends = build_backends(extraction_store.scratch_dir)

        triage_agent = build_triage_agent(loaded, backends=backends, extraction_store=extraction_store)
        triage_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Files to triage:\n" + "\n".join(file_paths),
                    }
                ]
            }
        )

        result_holder: dict[str, Any] = {}
        merge_agent = build_merge_agent(
            loaded, backends=backends, extraction_store=extraction_store, result_holder=result_holder
        )
        run_merge(merge_agent)

        def _repair(errors: list[str]) -> dict:
            error_summary = "\n".join(errors)
            run_merge(
                merge_agent,
                repair_note=(
                    "Your previous emit_final_output call failed schema validation "
                    f"with these errors:\n{error_summary}\nCall read_all_partials "
                    "again if needed and call emit_final_output again with a "
                    "corrected payload."
                ),
            )
            return result_holder.get("output", {})

        resolution = build_resolution_payload(extraction_store.flagged)

        validation = validate_and_repair(
            output=result_holder.get("output", {}),
            resolution=resolution,
            output_schema=loaded.output_schema,
            resolution_schema=loaded.resolution_schema,
            repair_fn=_repair,
            max_repair_turns=loaded.profile.max_repair_turns,
        )

        return PipelineResult(
            structured_output=validation.output,
            resolution=validation.resolution,
            validation=validation,
        )
    finally:
        extraction_store.cleanup()
