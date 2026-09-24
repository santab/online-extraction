# Online Extraction

A reusable, profile-driven extraction framework for mixed-format document intake.

This repository is not tied to a single domain. Instead, it provides a general pattern for:

- receiving an unknown mix of file types
- routing each file to the correct parser or modality
- extracting structured data into a schema-defined output
- reconciling conflicting values across sources
- validating results and surfacing unresolved fields for follow-up review

The invoice example included in this repo is just one concrete profile, not the core product definition.

## What this project does

- Accepts a mixed batch of documents with unknown composition
- Uses a triage agent to decide which modality should handle each file
- Extracts structured content from representative file types such as:
  - PDF
  - Excel
  - Images
  - DOCX
- Merges partial results into a single schema-driven payload
- Validates output against configurable schemas
- Produces both:
  - `structured_output.json`: the best available final structured result
  - `resolution.json`: a list of unresolved or low-confidence fields for downstream review

## Architecture at a glance

This project follows a hybrid design:

- Agentic orchestration for routing, planning, and conflict resolution
- Deterministic extraction and validation for the actual data transformation work

The design rationale is described in [docs/architecture.md](docs/architecture.md).

## Project layout

- [pyproject.toml](pyproject.toml): project metadata and Python dependencies
- [profiles/](profiles/): declarative use-case profiles and schema definitions
- [skills/](skills/): versioned skills used by agent behavior
- [src/extraction_agent](src/extraction_agent): main application code
- [tests/](tests/): unit tests for parsing, validation, and configuration
- [docker/Dockerfile](docker/Dockerfile): container build definition

## Core components

- `factory.py`: builds the configured extraction pipeline from a profile
- `graph.py`: orchestrates triage, modality execution, merge, and validation
- `config/`: schema and profile loading logic
- `modalities/`: implementations for each supported file type
- `agents/`: triage, merge, and validation agents
- `runtime/entrypoint.py`: CLI entry point for running a batch
- `runtime/publisher.py`: emits resolution artifacts for downstream consumers

## Profiles

This repo ships with an example profile for invoice-style intake, but the framework itself is domain-agnostic:

- [profiles/invoice-intake.yaml](profiles/invoice-intake.yaml)
- [profiles/schemas/invoice-intake.output.schema.json](profiles/schemas/invoice-intake.output.schema.json)

To adapt the system for another intake type, create a new profile and corresponding output schema without changing the core pipeline logic.

## Prerequisites

- Python 3.11+
- Git
- A model provider configured for the profile you are using

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Running the pipeline

The CLI entry point accepts a profile and one or more input files:

```bash
python -m extraction_agent.runtime.entrypoint \
  --profile profiles/invoice-intake.yaml \
  --files ./sample/doc1.pdf ./sample/doc2.xlsx \
  --out-dir ./output
```

This writes:

- `output/structured_output.json`
- `output/resolution.json`

## Example workflow

1. Define a profile for your target document type
2. Add the input files for the batch
3. Run the extraction CLI with that profile
4. Inspect the structured output and resolution records
5. Route any unresolved values to the appropriate human or downstream workflow

## Testing

Run the project test suite with:

```bash
pytest
```

## Design goals

This project intentionally separates:

- model-driven triage and merge logic
- deterministic extraction logic
- schema validation and repair

That separation keeps the project reusable, easier to test, and simpler to adapt to new document-processing use cases.

## License

This project is licensed under the [MIT License](LICENSE).
