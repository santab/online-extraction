from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import StructuredTool

from extraction_agent.tools.json_schema_models import json_schema_to_pydantic


def make_extraction_tool(
    *,
    name: str,
    description: str,
    schema: dict,
    on_result: Callable[[dict[str, Any]], str],
) -> StructuredTool:
    """Build the forced-tool-call an extraction sub-agent (or merge agent)
    must invoke to emit structured output. The tool's args_schema is derived
    from the profile's JSON Schema, so a schema-conforming call is the only
    way the model can "answer" — this is what makes extraction deterministic
    once the schema is fixed, per the no-free-text-JSON rule in the
    architecture doc.

    `on_result` receives the validated payload as a dict and does the actual
    side effect (write partial result to the extraction store, write final
    output, etc.) and returns a short string the agent sees as the tool result.
    """
    args_model = json_schema_to_pydantic(schema, model_name=f"{name}_args")

    def _run(**kwargs: Any) -> str:
        return on_result(kwargs)

    return StructuredTool.from_function(
        func=_run,
        name=name,
        description=description,
        args_schema=args_model,
    )
