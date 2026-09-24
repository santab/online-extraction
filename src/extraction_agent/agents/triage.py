from __future__ import annotations

from deepagents import create_deep_agent

from extraction_agent.backends import PipelineBackends, skills_deny_write_permission, to_virtual_skill_path
from extraction_agent.config.loader import LoadedProfile
from extraction_agent.config.models import resolve_model
from extraction_agent.modalities import get_modality
from extraction_agent.state import ExtractionStore
from extraction_agent.tools.file_inspect import inspect_file

_SYSTEM_PROMPT = """\
You triage a small, variable-composition batch of intake files (PDF, Excel,
image, DOCX — the exact mix is not known ahead of time).

For each file:
1. Use inspect_file to sniff its type.
2. Add a todo naming which modality sub-agent should handle it.
3. Delegate the file to that sub-agent via the task tool, passing the file
   path. The sub-agent will parse the file and record its own partial
   extraction — you do not extract fields yourself.

Process every file in the batch before finishing. Do not guess a file's
content instead of delegating to the sub-agent that can actually read it.

A "triage" skill is available with classification rules for ambiguous
files — check it before you start.
"""


def build_triage_agent(
    loaded: LoadedProfile,
    *,
    backends: PipelineBackends,
    extraction_store: ExtractionStore,
):
    profile = loaded.profile

    subagents = []
    for modality_name in profile.modalities:
        modality = get_modality(modality_name)
        skill_source = to_virtual_skill_path(profile.skill_path_for(modality_name))
        subagents.append(
            modality.build_subagent(
                model=profile.model_for(modality_name),
                output_schema=loaded.output_schema,
                backends=backends,
                skill_source=skill_source,
                on_partial_result=extraction_store.make_recorder(modality_name),
            )
        )

    return create_deep_agent(
        model=resolve_model(profile.model_for("triage")),
        tools=[inspect_file],
        subagents=subagents,
        system_prompt=_SYSTEM_PROMPT,
        skills=[to_virtual_skill_path(profile.skill_path_for("triage"))],
        permissions=[skills_deny_write_permission()],
        backend=backends.composite,
    )
