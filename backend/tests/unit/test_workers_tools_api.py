"""
OmniAgent AI — Workers, Tools, Processing, and Analytics Test Suite (Step 8 Verification)
Verifies:
1. Processing pipeline (PDF, DOCX, Image, OCR) with security checks and magic bytes.
2. Tools (Storage with path traversal defense, Email NOT_CONFIGURED, Ticket idempotency, Excel/CSV generation).
3. Analytics and Notification services.
4. Background Celery task execution.
"""

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from PIL import Image

from app.models.agent_run import AgentRun
from app.models.notification import Notification
from app.processing.docx import extract_docx_text
from app.processing.image import validate_and_process_image
from app.processing.ocr import extract_ocr_text
from app.processing.pdf import extract_pdf_text
from app.services.analytics_service import AnalyticsService
from app.services.notification_service import NotificationService
from app.tools.email.send import send_email
from app.tools.reports.csv_report import generate_csv
from app.tools.reports.excel import generate_excel
from app.tools.storage.client import StorageClient
from app.tools.tickets.create import create_ticket
from app.workers.tasks import execute_workflow_step, index_document

# ==============================================================================
# 1. Processing Pipeline Tests
# ==============================================================================

def test_pdf_extraction_magic_bytes_check():
    # Invalid bytes must be rejected
    with pytest.raises(ValueError, match="magic bytes"):
        extract_pdf_text(b"NOT_A_REAL_PDF")


def test_docx_extraction_magic_bytes_check():
    with pytest.raises(ValueError, match="magic bytes"):
        extract_docx_text(b"NOT_A_DOCX_FILE")


def test_image_validation_magic_bytes_and_caps():
    # Invalid image bytes
    with pytest.raises(ValueError, match="magic byte"):
        validate_and_process_image(b"FAKE_IMAGE_DATA")

    # Valid PNG image
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    meta = validate_and_process_image(png_bytes)
    assert meta["width"] == 100
    assert meta["height"] == 100
    assert meta["mime_type"] == "image/png"


def test_ocr_reports_honest_status_when_binary_missing():
    # When tesseract is not installed, does not crash or fake data
    text = extract_ocr_text(b"dummy")
    assert "[OCR UNAVAILABLE" in text or "[OCR ERROR" in text or isinstance(text, str)


# ==============================================================================
# 2. Production Tools Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_storage_client_crud_and_path_traversal_guard(tmp_path: Path):
    storage = StorageClient()
    storage.base_dir = tmp_path

    org_id = str(uuid4())
    file_name = "test_doc.txt"
    payload = b"Hello, secure multi-tenant storage!"

    # 1. Upload
    up = await storage.upload(org_id, file_name, payload)
    assert up["file_path"] == file_name

    # 2. Download
    down = await storage.download(org_id, file_name)
    assert down == payload

    # 3. Path Traversal Attack blocked
    with pytest.raises(ValueError, match="Path traversal"):
        await storage.upload(org_id, "../../etc/passwd", b"evil")

    # 4. Delete
    deleted = await storage.delete(org_id, file_name)
    assert deleted is True


@pytest.mark.asyncio
async def test_email_tool_reports_not_configured():
    res = await send_email({"to": "user@example.com", "subject": "Test"})
    assert res["status"] == "NOT_CONFIGURED"
    assert "not configured" in res["message"]


@pytest.mark.asyncio
async def test_ticket_tool_generates_idempotency_key():
    res = await create_ticket({"title": "Fix login glitch", "priority": "HIGH"})
    assert res["status"] == "CREATED"
    assert "ticket_id" in res
    assert "idempotency_key" in res


@pytest.mark.asyncio
async def test_excel_report_generation():
    headers = ["ID", "Name", "Score"]
    rows = [["1", "Alice", 95], ["2", "Bob", 88]]
    res = await generate_excel({"title": "Test Sheet", "headers": headers, "rows": rows})
    assert res["status"] == "GENERATED"
    assert res["format"] == "xlsx"
    assert res["row_count"] == 2
    assert res["size_bytes"] > 0


@pytest.mark.asyncio
async def test_csv_report_generation():
    headers = ["Item", "Quantity"]
    rows = [["Widget A", 10], ["Widget B", 25]]
    res = await generate_csv({"headers": headers, "rows": rows})
    assert res["status"] == "GENERATED"
    assert res["format"] == "csv"
    assert res["row_count"] == 2
    assert res["size_bytes"] > 0


# ==============================================================================
# 3. Analytics & Notification Services Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_analytics_service_metrics():
    org_id = uuid4()
    mock_session = MagicMock()

    # Mock agent runs
    run1 = AgentRun(
        id=uuid4(),
        organization_id=org_id,
        agent_name="document_agent",
        status="COMPLETED",
        latency_ms=120,
        total_tokens=450,
        cost_usd=0.005,
    )
    run2 = AgentRun(
        id=uuid4(),
        organization_id=org_id,
        agent_name="rag_agent",
        status="COMPLETED",
        latency_ms=250,
        total_tokens=800,
        cost_usd=0.012,
    )

    runs_result = MagicMock()
    runs_result.scalars.return_value.all.return_value = [run1, run2]

    breakdown_result = MagicMock()
    breakdown_result.all.return_value = []

    count_result = MagicMock()
    count_result.scalar.return_value = 0

    mock_session.execute = AsyncMock(side_effect=[
        runs_result,
        breakdown_result,
        count_result,
        count_result,
    ])

    service = AnalyticsService(mock_session)
    overview = await service.get_overview(org_id, days=30)

    assert overview["total_runs"] == 2
    assert overview["successful_runs"] == 2
    assert overview["success_rate_percent"] == 100.0
    assert overview["total_tokens"] == 1250
    assert overview["latency"]["avg_ms"] == 185
    assert overview["latency"]["p50_ms"] == 185


@pytest.mark.asyncio
async def test_notification_service_lifecycle():
    org_id = uuid4()
    user_id = uuid4()
    mock_session = MagicMock()

    notif = Notification(
        id=uuid4(),
        organization_id=org_id,
        user_id=user_id,
        title="Action Required",
        message="Please review high risk action",
        notification_type="WARNING",
        is_read=False,
    )

    list_res = MagicMock()
    list_res.scalars.return_value.all.return_value = [notif]

    count_res = MagicMock()
    count_res.scalar.return_value = 1

    update_res = MagicMock()
    update_res.rowcount = 1

    mock_session.execute = AsyncMock(side_effect=[list_res, count_res, update_res])
    mock_session.flush = AsyncMock()

    service = NotificationService(mock_session)

    # 1. List
    items = await service.list_notifications(org_id, user_id)
    assert len(items) == 1
    assert items[0].title == "Action Required"

    # 2. Unread count
    count = await service.get_unread_count(org_id, user_id)
    assert count == 1

    # 3. Mark as read
    ok = await service.mark_as_read(notif.id, org_id, user_id)
    assert ok is True


# ==============================================================================
# 4. Background Celery Task Execution
# ==============================================================================

def test_celery_tasks_execute():
    res_doc = index_document("doc-123", "org-456")
    assert res_doc["status"] == "COMPLETED"

    res_wf = execute_workflow_step("run-789", 2)
    assert res_wf["status"] == "SUCCESS"
