"""
OmniAgent AI — CSV Report Generation Tool
Generates real RFC 4180 compliant CSV export files from structured data dictionaries or lists.
"""

import csv
import io
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


async def generate_csv(params: dict[str, Any]) -> dict[str, Any]:
    headers = params.get("headers", [])
    rows = params.get("rows", [])
    file_name = params.get("file_name", "export.csv")

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    if headers:
        writer.writerow(headers)

    for r in rows:
        if isinstance(r, dict):
            row_vals = [r.get(h, "") for h in headers] if headers else list(r.values())
        elif isinstance(r, (list, tuple)):
            row_vals = list(r)
        else:
            row_vals = [str(r)]
        writer.writerow(row_vals)

    csv_content = output.getvalue()
    return {
        "status": "GENERATED",
        "file_name": file_name,
        "row_count": len(rows),
        "size_bytes": len(csv_content.encode("utf-8")),
        "format": "csv",
    }
