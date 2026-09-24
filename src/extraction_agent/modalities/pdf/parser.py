from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import tool
from pypdf import PdfReader


@dataclass
class PdfPage:
    index: int
    text: str
    has_text: bool
    embedded_image_count: int
    needs_visual_review: bool


def _page_embedded_image_count(page) -> int:
    try:
        return len(page.images)
    except Exception:
        # Older pypdf without .images, or a malformed page — treat as
        # unknown rather than crashing the whole parse.
        return 0


def _needs_visual_review(has_text: bool, embedded_image_count: int) -> bool:
    return (not has_text) or embedded_image_count > 0


def parse_pdf_pages(file_path: str) -> list[PdfPage]:
    """Per-page analysis, not just a flat text dump: a page can have
    extractable text AND an embedded image carrying separate information
    (a stamp, a signature, a logo with an embedded code, a table rendered
    as a picture) — flattening straight to text would silently drop that.

    `needs_visual_review` is True when a page has no extractable text
    (likely scanned) OR has any embedded image alongside text (mixed
    layout) — either way a page-to-image + VLM pass may see fields the text
    layer doesn't have.

    NOTE: doesn't detect Type-3 fonts specifically (pypdf extracts *some*
    garbled/wrong text from them rather than raising or returning empty, so
    `has_text=True` can still be misleading for those). Treat sub-agent
    field reads with unexpected characters/formatting as a signal to fall
    back to the image path even when has_text=True — see skills/pdf.
    """
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        has_text = len(text.strip()) > 0
        image_count = _page_embedded_image_count(page)
        pages.append(
            PdfPage(
                index=i,
                text=text,
                has_text=has_text,
                embedded_image_count=image_count,
                needs_visual_review=_needs_visual_review(has_text, image_count),
            )
        )
    return pages


def pdf_page_to_image(file_path: str, page_index: int) -> bytes:
    """TODO: render `page_index` of `file_path` to a PNG (e.g. via pypdfium2
    or pdf2image) so flagged pages (see PdfPage.needs_visual_review) can be
    handed to the same VLM call the image sub-agent uses, instead of
    maintaining a separate OCR path — OCR is unreliable for scanned pages
    and Type-3 fonts, so VLM is the primary strategy here, not a fallback of
    last resort."""
    raise NotImplementedError("page-to-image fallback not yet implemented")


@tool
def parse_pdf(file_path: str) -> dict:
    """Extract per-page text and flag pages that need a visual (VLM) pass in
    addition to or instead of the text layer — either because no text was
    extracted (likely scanned) or because the page has embedded images that
    may carry fields the text layer doesn't."""
    pages = parse_pdf_pages(file_path)
    return {
        "file_path": str(Path(file_path)),
        "page_count": len(pages),
        "pages": [
            {
                "index": p.index,
                "text": p.text,
                "has_text": p.has_text,
                "embedded_image_count": p.embedded_image_count,
                "needs_visual_review": p.needs_visual_review,
            }
            for p in pages
        ],
        "pages_needing_visual_review": [p.index for p in pages if p.needs_visual_review],
    }
