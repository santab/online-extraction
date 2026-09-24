from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.tools import tool


def list_sheets(file_path: str) -> list[str]:
    return pd.ExcelFile(file_path).sheet_names


@tool
def parse_excel(file_path: str, sheet_name: str | None = None) -> dict:
    """List sheets in a workbook, or load one sheet as records. Call with no
    sheet_name first to see what's available (a workbook may have several
    sheets, only some of which are relevant)."""
    path = Path(file_path)
    sheets = list_sheets(str(path))

    if sheet_name is None:
        return {"file_path": str(path), "sheets": sheets}

    df = pd.read_excel(path, sheet_name=sheet_name)
    return {
        "file_path": str(path),
        "sheet_name": sheet_name,
        "columns": list(df.columns.astype(str)),
        # TODO: guard against very large sheets blowing up agent context —
        # truncate/summarize rows beyond some threshold instead of dumping
        # the whole sheet.
        "rows": df.to_dict(orient="records"),
    }
