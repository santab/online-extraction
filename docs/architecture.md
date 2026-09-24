# Extraction Agent — Architecture & Design Decisions

## Problem
Given a small, variable-composition batch (<10 files: PDF, Excel, image, DOCX) of
unknown mix per intake, extract information and produce a structured JSON output
conforming to a schema. Today a human triages the documents and fills the form by
hand; this module replaces that triage + extraction step.

## Why agentic, and where exactly
The file mix is not known in advance (could be 3 PDFs one day, 2 PDFs + an Excel +
a photo the next), so *routing/triage* is genuinely non-deterministic and needs an
agent making judgment calls. Everything downstream of "which extractor handles
this file" is deterministic and should NOT be agentic:
- Field extraction per file → deterministic schema-constrained tool call
- Final JSON assembly → deterministic schema-constrained tool call
- Schema validation → deterministic code, no LLM

Agentic judgment is reserved for: (1) triage/planning across an unknown file mix,
and (2) reconciling conflicting values across sources during merge.

## Pipeline stages
1. **Intake** — files arrive, count/format unknown ahead of time.
2. **Triage agent** (agentic) — inspects what arrived, writes a todo per file
   naming which modality sub-agent should handle it.
3. **Modality sub-agents** (deterministic tool calls, run in parallel) — one per
   file type: PDF, Excel, Image, Doc. Each extracts fields into a *partial*
   schema via forced tool-calling (never free-text JSON).
4. **Extraction store** — partial per-file results with source pointers and
   confidence, held in agent state (not real disk).
5. **Merge agent** (agentic) — reconciles conflicts across sources, fills the
   full output schema. Where it can't resolve a field confidently, it calls a
   `flag_field` tool that records the field, candidate values, sources, and
   confidence — a plain data-recording call, **not** an interrupt.
6. **Validate & repair** (deterministic) — validates output against both the
   main schema and the resolution-list schema; one repair turn on failure.
7. **Terminal output — always both, no branching:**
   - `structured_output.json` — full schema, best-available values, with a
     per-field `needs_review` flag where confidence was low.
   - `resolution.json` — flat list of unresolved fields (field name,
     candidates, source, reason: missing / conflicting / low-confidence).

## Explicit boundary: no human-in-the-loop inside this module
This module always runs to completion and never pauses on `interrupt_on`. It
publishes `resolution.json` (e.g. to a queue/topic) and its job ends there.
Picking it up, routing to a person, and resolving it is a **separate,
event-driven system**, out of scope for this repo. Open question not yet
decided: whether a human correction re-enters this module to regenerate the
structured output, or whether the external system patches the record itself.

## Framework
`langchain-ai/deepagents` (Deep Agents). Chosen because triage/merge need
planning + sub-agent delegation + context isolation per file, which are its
core primitives — this is NOT used for open-ended research-style tasks here,
just the orchestration layer of an otherwise deterministic pipeline.

## Backend strategy (CompositeBackend, not one FilesystemBackend for everything)
- `/skills/` → read-only `FilesystemBackend`, `virtual_mode=True`,
  `FilesystemPermission` denies writes. Baked into the container image at
  build time — skills are a design-time, versioned artifact, never edited at
  runtime.
- Scratch/working data (todos, extraction store) → `StateBackend`, riding on a
  **durable LangGraph checkpointer** (Postgres) for crash/retry recovery.
- Raw input files → object storage (S3-compatible) via a custom tool, not
  container-local disk — the container is stateless per invocation.
- No `Sandbox`/`LocalShellBackend`/`execute` tool. All extraction tools are
  fixed pre-built Python functions; the agent never writes or runs arbitrary
  code, which closes off the largest attack surface a filesystem-backed agent
  normally carries.

## Runtime
Python, Linux container, multi-stage build. Non-root user, read-only root
filesystem except `/tmp` scratch. Egress allowlist: model provider API +
object store/checkpointer DB only. No OCR system deps if using a VLM call for
the image sub-agent instead of local Tesseract.

## Tools per agent
| Agent | Tools |
|---|---|
| Triage | built-in `write_todos`, filesystem ops, `task` (delegation); custom file-inspection tool (mime/type sniff, cheap peek) |
| PDF sub-agent | layout-aware PDF parser, page-to-image fallback, partial schema-extraction tool, filesystem write |
| Excel sub-agent | spreadsheet loader (pandas/openpyxl), sheet-lister, partial schema-extraction tool, filesystem write |
| Image sub-agent | VLM or OCR call, image preprocessing, partial schema-extraction tool, filesystem write |
| Doc sub-agent | DOCX parser (python-docx/mammoth), partial schema-extraction tool, filesystem write |
| Merge | filesystem read (all partials), final schema-extraction tool, `flag_field` tool (data recording, not interrupt) |
| Validate & repair | schema validator (Pydantic/jsonschema) — deterministic code, not an LLM agent |

## Skills (design-time, one per agent that needs judgment)
- `skills/triage/` — classification rules for ambiguous files, todo-naming
  convention.
- `skills/pdf/`, `skills/excel/`, `skills/image/`, `skills/docx/` — format
  parsing gotchas (merged cells, multi-column layout, OCR vs VLM trust
  thresholds).
- `skills/merge/` — source-of-truth / conflict-resolution rules. This is
  business logic that varies per org/profile and should be editable without
  touching agent code.

## Repo structure
```
extraction-agent/
├── pyproject.toml
├── src/extraction_agent/
│   ├── factory.py          # builds create_deep_agent(...) from a Profile
│   ├── graph.py             # triage → sub-agents → merge → validate
│   ├── config/{schema.py, loader.py}   # Profile model + YAML loader
│   ├── modalities/          # one plugin per file type — extensibility seam
│   │   ├── base.py          # Modality protocol
│   │   ├── pdf/ excel/ image/ docx/
│   ├── agents/{triage.py, merge.py, validate.py}
│   ├── schemas/resolution.py
│   ├── backends.py          # CompositeBackend wiring
│   └── runtime/{entrypoint.py, publisher.py}
├── skills/                  # baked into image at build time
├── profiles/                # declarative per-use-case config (YAML)
├── evals/fixtures/          # one fixture set per profile
├── docker/Dockerfile
└── tests/
```

A **profile** (e.g. `profiles/invoice-intake.yaml`) declares: which modalities
apply, the output schema, the resolution schema, model, and which skill paths
to load — this is what a new use case actually configures, without touching
pipeline code.

## Open decisions (not yet resolved — flag if revisiting)
- Schema registry format: Pydantic classes vs. raw JSON Schema files (affects
  whether non-Python teams can contribute a profile).
- Skill/profile versioning: pin skill versions per profile so an edit for one
  tenant doesn't silently regress another.
- Per-profile eval coverage: shared generic eval corpus won't catch
  profile-specific regressions.
- Whether a human's resolution re-enters this module to regenerate output, or
  the external HIL system patches the record independently.
