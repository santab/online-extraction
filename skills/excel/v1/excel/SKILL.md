---
name: excel
description: Format-parsing gotchas for reading spreadsheet workbooks (sheet selection, merged cells) when extracting fields from Excel/CSV input files.
---

# Excel sub-agent skill

Format-parsing gotchas for `parse_excel`'s output.

- Call with no `sheet_name` first — a workbook may have several sheets and
  only one or two are relevant to the output schema.
- Merged cells appear as the value on their first cell only and blank/NaN on
  the rest; don't treat a blank as "field missing" without checking whether
  it's a merge continuation.

<!-- TODO: fill in with real per-profile spreadsheet layout gotchas. -->
