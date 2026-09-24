---
name: triage
description: Classification rules for routing an unknown mix of intake files (PDF, Excel, image, DOCX) to the right modality sub-agent, and the todo-naming convention to follow while doing it.
---

# Triage skill

Classification rules for ambiguous files, and the todo-naming convention the
triage agent should follow.

- A file's extension is a hint, not ground truth — `inspect_file`'s
  `suggested_modality` can be wrong (e.g. a scanned PDF should sometimes go
  to the image sub-agent's VLM path instead of the PDF text parser).
- One todo per file, named `<modality>: <file_path>`.
- If a file's type genuinely can't be determined, delegate it to the
  modality suggested by `inspect_file` anyway and let that sub-agent fail
  fast rather than guessing further at the triage level.

<!-- TODO: fill in with real per-org classification rules. -->
