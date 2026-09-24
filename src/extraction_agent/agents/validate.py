from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from jsonschema.validators import validator_for


def validate_against_schema(payload: dict, schema: dict) -> list[str]:
    """Deterministic validation, no LLM involved — this is the
    "Validate & repair" stage's non-agentic half."""
    validator_cls = validator_for(schema)
    validator = validator_cls(schema)
    return [f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in validator.iter_errors(payload)]


@dataclass
class ValidationResult:
    output: dict
    output_errors: list[str]
    resolution: dict
    resolution_errors: list[str]
    repair_attempts: int


def validate_and_repair(
    *,
    output: dict,
    resolution: dict,
    output_schema: dict,
    resolution_schema: dict,
    repair_fn: Callable[[list[str]], dict],
    max_repair_turns: int = 1,
) -> ValidationResult:
    """One repair turn on failure, per the architecture doc — not an
    open-ended retry loop. `repair_fn` re-invokes the merge agent with the
    validation errors and returns its (possibly still invalid) output."""
    errors = validate_against_schema(output, output_schema)
    attempts = 0
    while errors and attempts < max_repair_turns:
        output = repair_fn(errors)
        errors = validate_against_schema(output, output_schema)
        attempts += 1

    resolution_errors = validate_against_schema(resolution, resolution_schema)
    return ValidationResult(
        output=output,
        output_errors=errors,
        resolution=resolution,
        resolution_errors=resolution_errors,
        repair_attempts=attempts,
    )
