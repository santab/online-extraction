import pytest
from pydantic import ValidationError

from extraction_agent.tools.json_schema_models import json_schema_to_pydantic

SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "total_amount": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["description", "amount"],
            },
        },
    },
    "required": ["invoice_number"],
}


def test_required_field_enforced():
    Model = json_schema_to_pydantic(SCHEMA, "Invoice")
    with pytest.raises(ValidationError):
        Model()


def test_optional_field_defaults_to_none():
    Model = json_schema_to_pydantic(SCHEMA, "Invoice")
    instance = Model(invoice_number="INV-1")
    assert instance.total_amount is None


def test_nested_array_of_objects_round_trips():
    Model = json_schema_to_pydantic(SCHEMA, "Invoice")
    instance = Model(
        invoice_number="INV-1",
        line_items=[{"description": "widget", "amount": 9.99}],
    )
    assert instance.line_items[0].description == "widget"
    assert instance.line_items[0].amount == 9.99


def test_rejects_non_object_root_schema():
    with pytest.raises(ValueError):
        json_schema_to_pydantic({"type": "string"}, "NotAnObject")
