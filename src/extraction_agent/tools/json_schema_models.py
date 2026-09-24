from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, create_model

_TYPE_MAP: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}

_counter = 0


def _unique_name(prefix: str) -> str:
    global _counter
    _counter += 1
    return f"{prefix}_{_counter}"


def json_schema_to_pydantic(schema: dict, model_name: str = "GeneratedModel") -> type[BaseModel]:
    """Build a Pydantic model from a JSON Schema object so it can be used as
    an LLM tool's args_schema for forced tool-calling.

    Covers the subset of JSON Schema profiles actually need for extraction
    targets: object/array/string/integer/number/boolean, enum, required,
    nested objects and arrays-of-objects. Does NOT handle $ref, oneOf/anyOf/
    allOf, or conditional schemas — extend here if a profile's schema needs
    them.
    """
    if schema.get("type") != "object":
        raise ValueError("root schema must be type=object to become a tool args_schema")
    return _object_to_model(schema, model_name)


def _object_to_model(schema: dict, model_name: str) -> type[BaseModel]:
    properties: dict = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields: dict[str, tuple[Any, Any]] = {}

    for prop_name, prop_schema in properties.items():
        py_type = _resolve_type(prop_schema, f"{model_name}_{prop_name}")
        is_required = prop_name in required
        default = ... if is_required else None
        if not is_required:
            py_type = py_type | None
        fields[prop_name] = (py_type, Field(default, description=prop_schema.get("description")))

    return create_model(model_name, **fields)  # type: ignore[call-overload]


def _resolve_type(prop_schema: dict, name_hint: str) -> Any:
    if "enum" in prop_schema:
        from enum import Enum

        enum_cls = Enum(_unique_name(name_hint), {str(v): v for v in prop_schema["enum"]})
        return enum_cls

    json_type = prop_schema.get("type")

    if json_type == "object":
        return _object_to_model(prop_schema, _unique_name(name_hint))

    if json_type == "array":
        items_schema = prop_schema.get("items", {})
        item_type = _resolve_type(items_schema, _unique_name(f"{name_hint}_item"))
        return list[item_type]  # type: ignore[valid-type]

    if json_type in _TYPE_MAP:
        return _TYPE_MAP[json_type]

    return Any
