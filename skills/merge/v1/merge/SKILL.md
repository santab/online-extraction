---
name: merge
description: Source-of-truth and conflict-resolution rules for reconciling per-file partial extractions into the final output, including when to flag a field instead of guessing.
---

# Merge skill

Source-of-truth / conflict-resolution rules. This is business logic that
varies per org/profile — edit this file per deployment without touching
agent code.

- Default source priority when sources conflict and nothing else breaks the
  tie: prefer the modality least prone to transcription error for that field
  type (e.g. Excel/DOCX text over OCR/VLM-read values for numeric fields).
- Always call `flag_field` on a conflict even if you picked a value —
  resolution is for human awareness, not just for fields left blank.

<!-- TODO: fill in with real per-profile source-priority rules. -->
