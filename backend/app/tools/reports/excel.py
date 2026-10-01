"""
OmniAgent AI — Excel Report Generation Tool
Generates real, styled .xlsx spreadsheet workbooks from structured JSON dataset records using openpyxl.
"""

import io
from typing import Any

import structlog
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

logger = structlog.get_logger(__name__)


async def generate_excel(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generates a valid Excel spreadsheet bytes buffer from data rows and column headers.
    """
    title = params.get("title", "Export Report")
    headers = params.get("headers", [])
    rows = params.get("rows", [])

    wb = Workbook()
    ws = wb.active
    ws.title = title[:30]

    # Format header
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")

    if headers:
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

    # Append data rows
    for r in rows:
        if isinstance(r, dict):
            row_vals = [r.get(h, "") for h in headers] if headers else list(r.values())
        elif isinstance(r, (list, tuple)):
            row_vals = list(r)
        else:
            row_vals = [str(r)]
        ws.append(row_vals)

    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()

    file_name = params.get("file_name", "report.xlsx")
    return {
        "status": "GENERATED",
        "file_name": file_name,
        "row_count": len(rows),
        "size_bytes": len(excel_bytes),
        "format": "xlsx",
    }
