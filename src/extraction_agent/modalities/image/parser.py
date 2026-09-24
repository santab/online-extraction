from __future__ import annotations

import base64
import io
from pathlib import Path

from langchain_core.tools import tool
from PIL import Image

_MAX_DIMENSION = 2048


def preprocess_image(file_path: str) -> bytes:
    """Deterministic preprocessing: downscale oversized images and normalize
    to PNG so the VLM call gets a consistent input regardless of source
    format/orientation."""
    img = Image.open(file_path)
    img = img.convert("RGB")
    if max(img.size) > _MAX_DIMENSION:
        img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@tool
def load_image(file_path: str) -> dict:
    """Preprocess an image file and return it as base64 PNG for the
    sub-agent's multimodal model call.

    NOTE: architecture doc leaves VLM-vs-OCR as an open decision. This tool
    only does preprocessing; the actual field-reading happens via the
    sub-agent's own multimodal model turn (image attached to the message),
    not a separate tool call. If OCR is chosen instead, add an `ocr_image`
    tool here rather than replacing this one, since preprocessing is needed
    either way.
    """
    png_bytes = preprocess_image(file_path)
    return {
        "file_path": str(Path(file_path)),
        "image_base64": base64.b64encode(png_bytes).decode("ascii"),
        "mime_type": "image/png",
    }
