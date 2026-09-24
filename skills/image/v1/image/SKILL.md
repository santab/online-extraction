---
name: image
description: Why field-reading from images and scanned/Type-3-font PDF pages should default to a VLM pass rather than OCR, and how to handle mixed text/image layouts.
---

# Image sub-agent skill

OCR vs VLM decision (was open in architecture.md, now settled) and
preprocessing notes.

- **Default to VLM, not OCR**, for reading fields from images — including
  scanned-document pages and any page/embedded image using Type-3 fonts.
  Classic OCR is unreliable on both: scans degrade OCR accuracy directly,
  and Type-3 fonts have no standard character encoding to map glyphs back
  to text, so OCR (and even naive PDF text extraction) can silently return
  wrong or garbled characters instead of failing loudly.
- `load_image` only preprocesses (downscale + normalize to PNG); field
  reading happens in your own multimodal turn on the attached image, not a
  separate OCR tool call.
- A page or image can combine a text layer with embedded pictures that
  carry their own information (stamps, signatures, logos, a table rendered
  as a picture) — read the image itself, don't assume the text layer
  already covers everything visible on the page.
- Treat any field read from a low-resolution or heavily skewed image as
  low-confidence by default — call the extraction tool but expect merge to
  flag it unless another source corroborates it.

<!-- TODO: if a fast/cheap path is ever needed for high-volume, purely
     typed (non-scanned, non-Type-3) documents, OCR could be added as an
     optional pre-filter — but it must never be the only read for a flagged
     page, only VLM output should be trusted as the field-level answer. -->
