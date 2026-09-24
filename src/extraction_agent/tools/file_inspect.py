from __future__ import annotations

import mimetypes
from pathlib import Path

from langchain_core.tools import tool

_PEEK_BYTES = 512

_EXTENSION_TO_MODALITY = {
    ".pdf": "pdf",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "excel",
    ".docx": "docx",
    ".doc": "docx",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tiff": "image",
    ".bmp": "image",
}


def _guess_modality(path: Path, mime_type: str | None) -> str | None:
    if path.suffix.lower() in _EXTENSION_TO_MODALITY:
        return _EXTENSION_TO_MODALITY[path.suffix.lower()]
    if mime_type:
        if mime_type == "application/pdf":
            return "pdf"
        if mime_type.startswith("image/"):
            return "image"
    return None


@tool
def inspect_file(file_path: str) -> dict:
    """Cheap peek at a file so triage can decide which modality sub-agent
    should handle it: mime/type sniff by extension + magic bytes, size, and
    a small preview. Does not parse the file's actual content."""
    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    size = path.stat().st_size if path.exists() else None

    preview = b""
    if path.exists():
        with path.open("rb") as fh:
            preview = fh.read(_PEEK_BYTES)

    return {
        "file_path": str(path),
        "mime_type": mime_type,
        "size_bytes": size,
        "suggested_modality": _guess_modality(path, mime_type),
        "magic_bytes_hex": preview[:16].hex(),
    }
