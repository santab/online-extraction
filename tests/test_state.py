from extraction_agent.schemas.resolution import UnresolvedField
from extraction_agent.state import ExtractionStore


def test_recorder_attributes_partial_to_source_file():
    store = ExtractionStore()
    record = store.make_recorder("pdf")

    record({"source_file": "invoice.pdf", "invoice_number": "INV-1"})

    assert len(store.partials) == 1
    partial = store.partials[0]
    assert partial.source_modality == "pdf"
    assert partial.source_file == "invoice.pdf"
    assert partial.fields == {"invoice_number": "INV-1"}


def test_flag_records_unresolved_field():
    store = ExtractionStore()
    store.flag(UnresolvedField(field="total_amount", reason="missing"))

    assert len(store.flagged) == 1
    assert store.flagged[0].field == "total_amount"
