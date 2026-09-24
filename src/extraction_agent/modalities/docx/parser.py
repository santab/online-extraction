from __future__ import annotations

from pathlib import Path

import docx
from langchain_core.tools import tool


@tool
def parse_docx(file_path: str) -> dict:
    """Extract paragraph text and table contents from a DOCX file."""
    path = Path(file_path)
    document = docx.Document(str(path))

    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    tables = [
        [[cell.text for cell in row.cells] for row in table.rows]
        for table in document.tables
    ]

    return {
        "file_path": str(path),
        "paragraphs": paragraphs,
        "tables": tables,
    }
