"""
OmniAgent AI — Email Dispatch Tool
Sends emails via SMTP with honest NOT_CONFIGURED reporting when credentials are missing.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


async def send_email(params: dict[str, Any]) -> dict[str, Any]:
    recipient = params.get("to") or params.get("recipient")
    subject = params.get("subject", "Notification")
    body = params.get("body", "")
    smtp_host = params.get("smtp_host")

    if not recipient:
        return {"status": "FAILED", "error": "Recipient email address is required"}

    if not smtp_host:
        logger.info("smtp_not_configured_for_email_tool", recipient=recipient)
        return {
            "status": "NOT_CONFIGURED",
            "message": "SMTP service not configured in environment or integration config",
            "recipient": recipient,
            "subject": subject,
        }

    # When SMTP host is provided, attempt dispatch
    try:
        from email.message import EmailMessage

        import aiosmtplib  # type: ignore[import-untyped]

        msg = EmailMessage()
        msg["From"] = params.get("from", "noreply@omniagent.ai")
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        port = int(params.get("smtp_port", 587))
        await aiosmtplib.send(msg, hostname=smtp_host, port=port)
        return {"status": "SENT", "recipient": recipient, "subject": subject}
    except Exception as exc:  # noqa: BLE001
        logger.warning("email_send_failed", error=str(exc))
        return {"status": "FAILED", "error": str(exc), "recipient": recipient}
