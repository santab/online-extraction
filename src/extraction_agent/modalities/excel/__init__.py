from __future__ import annotations

from typing import Any, Callable

from extraction_agent.backends import PipelineBackends
from extraction_agent.config.schema import ModelConfig
from extraction_agent.modalities.base import make_modality_subagent
from extraction_agent.modalities.excel.parser import parse_excel

name = "excel"


def build_subagent(
    *,
    model: ModelConfig,
    output_schema: dict,
    backends: PipelineBackends,
    skill_source: str,
    on_partial_result: Callable[[dict[str, Any]], str],
) -> dict:
    return make_modality_subagent(
        name="excel",
        description="Extracts fields from a single Excel/CSV workbook.",
        parser_tool=parse_excel,
        model=model,
        output_schema=output_schema,
        skill_source=skill_source,
        on_partial_result=on_partial_result,
    )
