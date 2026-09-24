---
name: pdf
description: Layout-aware handling of PDF extraction, including when a page's text layer isn't enough and a visual (VLM) pass is needed instead of or alongside it.
---

# PDF sub-agent skill

Format-parsing gotchas for `parse_pdf`'s output.

- Check `pages_needing_visual_review`, not just whether the whole document
  has text — a page can have real extractable text AND an embedded image
  carrying separate information (a stamp, a signature, a total written over
  a printed table). Don't treat "this page has text" as "this page is
  fully covered by the text layer."
- OCR is not the default strategy here — it's unreliable for scanned pages
  and for Type-3 fonts (which pypdf can extract as garbled or wrong
  characters rather than failing outright). Prefer a VLM pass (via
  page-to-image, once implemented) on any flagged page, and treat unusual
  characters or formatting in text-layer output as a signal to fall back to
  the visual read even when `has_text=True`.
- Multi-column layouts can interleave text out of reading order — treat
  adjacent lines with suspicion if a field's expected format doesn't match.

<!-- TODO: fill in with real per-profile PDF layout gotchas. -->
