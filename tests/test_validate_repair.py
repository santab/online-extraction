from extraction_agent.agents.validate import validate_against_schema, validate_and_repair

SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "total_amount": {"type": "number"},
    },
    "required": ["invoice_number", "total_amount"],
}

RESOLUTION_SCHEMA = {
    "type": "object",
    "properties": {
        "unresolved_fields": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["unresolved_fields"],
}


def test_valid_payload_has_no_errors():
    assert validate_against_schema({"invoice_number": "INV-1", "total_amount": 1.0}, SCHEMA) == []


def test_missing_required_field_reported():
    errors = validate_against_schema({"invoice_number": "INV-1"}, SCHEMA)
    assert any("total_amount" in e for e in errors)


def test_repair_fn_invoked_once_and_result_used():
    calls = []

    def repair_fn(errors):
        calls.append(errors)
        return {"invoice_number": "INV-1", "total_amount": 1.0}

    result = validate_and_repair(
        output={"invoice_number": "INV-1"},
        resolution={"unresolved_fields": []},
        output_schema=SCHEMA,
        resolution_schema=RESOLUTION_SCHEMA,
        repair_fn=repair_fn,
        max_repair_turns=1,
    )

    assert len(calls) == 1
    assert result.output_errors == []
    assert result.repair_attempts == 1


def test_repair_not_invoked_when_already_valid():
    def repair_fn(errors):
        raise AssertionError("repair_fn should not be called")

    result = validate_and_repair(
        output={"invoice_number": "INV-1", "total_amount": 1.0},
        resolution={"unresolved_fields": []},
        output_schema=SCHEMA,
        resolution_schema=RESOLUTION_SCHEMA,
        repair_fn=repair_fn,
        max_repair_turns=1,
    )

    assert result.repair_attempts == 0
    assert result.output_errors == []


def test_stops_after_max_repair_turns_even_if_still_invalid():
    def repair_fn(errors):
        return {"invoice_number": "INV-1"}  # still missing total_amount

    result = validate_and_repair(
        output={},
        resolution={"unresolved_fields": []},
        output_schema=SCHEMA,
        resolution_schema=RESOLUTION_SCHEMA,
        repair_fn=repair_fn,
        max_repair_turns=1,
    )

    assert result.repair_attempts == 1
    assert result.output_errors != []
