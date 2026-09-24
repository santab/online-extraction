---
name: docx
description: Format-parsing gotchas for reading Word documents (table structure, paragraph ordering) when extracting fields from DOCX input files.
---

# DOCX sub-agent skill

Format-parsing gotchas for `parse_docx`'s output.

- Tables come back as raw row/cell text grids — header rows aren't
  distinguished from data rows, infer from content.
- Paragraph order follows document order, not visual layout, so text boxes
  and multi-column sections may appear out of visual sequence.

<!-- TODO: fill in with real per-profile DOCX layout gotchas. -->
