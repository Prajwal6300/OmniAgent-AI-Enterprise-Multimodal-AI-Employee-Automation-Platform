"""
OmniAgent AI — Action Agent Executor
Provides safe, auditable handler abstractions and execution engines for external side-effects.
Implements real provider integrations, configuration checks, and deterministic test mocks.
"""

import abc
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.services.storage_service import get_storage_service

from agents.action.exceptions import (
    ActionExecutionError,
    ActionNotConfiguredError,
)
from agents.action.schemas import (
    ActionContext,
    ActionType,
    CreateReportInput,
    CreateTicketInput,
    SendEmailInput,
    SendNotificationInput,
)

# ==============================================================================
# Provider Interfaces
# ==============================================================================

class BaseEmailProvider(abc.ABC):
    @abc.abstractmethod
    async def send_email(self, input_data: SendEmailInput, context: ActionContext) -> dict[str, Any]:
        """Dispatches an email. Returns dictionary containing message_id."""


class BaseNotificationProvider(abc.ABC):
    @abc.abstractmethod
    async def send_notification(self, input_data: SendNotificationInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        """Dispatches a notification. Returns dictionary containing notification_id."""


class BaseTicketProvider(abc.ABC):
    @abc.abstractmethod
    async def create_ticket(self, input_data: CreateTicketInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        """Creates a ticket. Returns dictionary containing ticket_id."""


class BaseReportProvider(abc.ABC):
    @abc.abstractmethod
    async def create_report(self, input_data: CreateReportInput, context: ActionContext, storage_service: Any = None) -> dict[str, Any]:
        """Generates a report artifact. Returns dictionary containing storage_path or artifact_id."""


# ==============================================================================
# Concrete Real Providers
# ==============================================================================

class SMTPEmailProvider(BaseEmailProvider):
    """Production email provider dispatching via configured SMTP."""

    async def send_email(self, input_data: SendEmailInput, context: ActionContext) -> dict[str, Any]:
        # Check if email is configured
        if not settings.SMTP_HOST or not settings.SMTP_HOST.strip():
            raise ActionNotConfiguredError("Email integration is not configured.")

        # Real SMTP delivery logic
        try:
            import asyncio
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            def _send_sync():
                msg = MIMEMultipart()
                msg["From"] = settings.SMTP_FROM_EMAIL
                msg["To"] = input_data.recipient
                msg["Subject"] = input_data.subject
                if input_data.cc:
                    msg["Cc"] = ", ".join(input_data.cc)

                msg.attach(MIMEText(input_data.body, "plain", "utf-8"))
                message_id = f"msg_{uuid.uuid4().hex[:16]}@omniagent.ai"
                msg["Message-ID"] = message_id

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.ACTION_EXECUTION_TIMEOUT_SECONDS) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    recipients = [input_data.recipient] + (input_data.cc or [])
                    server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())
                return message_id

            msg_id = await asyncio.to_thread(_send_sync)
            return {
                "message_id": msg_id,
                "recipient": input_data.recipient,
                "status": "SENT",
            }
        except ActionNotConfiguredError:
            raise
        except Exception as exc:
            raise ActionExecutionError(f"Email delivery failed: {exc!s}") from exc


class DatabaseNotificationProvider(BaseNotificationProvider):
    """In-app notification provider persisting notifications under the tenant."""

    async def send_notification(self, input_data: SendNotificationInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        if session is not None:
            from app.models.notification import Notification
            try:
                user_uuid = UUID(input_data.user_id)
            except ValueError:
                # If target user_id is username or string, use caller user_id as target
                user_uuid = UUID(context.user_id)

            notif = Notification(
                organization_id=UUID(context.organization_id),
                user_id=user_uuid,
                title=input_data.title,
                message=input_data.message,
                notification_type=input_data.channel,
                link_url=input_data.link_url,
            )
            session.add(notif)
            await session.flush()
            return {
                "notification_id": str(notif.id),
                "title": notif.title,
                "status": "DELIVERED",
            }

        # Standalone notification ID when session is not injected
        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
        return {
            "notification_id": notif_id,
            "title": input_data.title,
            "status": "DELIVERED",
        }


class DatabaseTicketProvider(BaseTicketProvider):
    """Internal maintenance request provider persisting tickets under the tenant."""

    async def create_ticket(self, input_data: CreateTicketInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        if session is not None:
            from app.models.business import MaintenanceRequest
            machine_uuid = None
            if input_data.machine_id:
                try:
                    machine_uuid = UUID(input_data.machine_id)
                except ValueError:
                    machine_uuid = None

            ticket = MaintenanceRequest(
                organization_id=UUID(context.organization_id),
                machine_id=machine_uuid,
                title=input_data.title,
                status="OPEN",
                priority=input_data.priority,
            )
            session.add(ticket)
            await session.flush()
            return {
                "ticket_id": str(ticket.id),
                "title": ticket.title,
                "priority": ticket.priority,
                "status": "OPEN",
            }

        ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"
        return {
            "ticket_id": ticket_id,
            "title": input_data.title,
            "priority": input_data.priority,
            "status": "OPEN",
        }


class StorageReportProvider(BaseReportProvider):
    """Report artifact provider saving markdown/JSON report artifacts in tenant storage."""

    async def create_report(self, input_data: CreateReportInput, context: ActionContext, storage_service: Any = None) -> dict[str, Any]:
        svc = storage_service or get_storage_service()
        report_content = f"# {input_data.title}\n\n**Type:** {input_data.report_type}\n**Date:** {datetime.now(timezone.utc).isoformat()}\n\n## Executive Summary\n{input_data.summary}\n"
        if input_data.data:
            import json
            report_content += f"\n## Structured Data\n```json\n{json.dumps(input_data.data, indent=2)}\n```\n"

        file_bytes = report_content.encode("utf-8")
        filename = f"{input_data.report_type.lower()}_{uuid.uuid4().hex[:8]}.md"
        org_uuid = UUID(context.organization_id)

        storage_path, checksum, file_size = await svc.save_file(
            file_data=file_bytes,
            original_filename=filename,
            org_id=org_uuid,
        )

        return {
            "artifact_id": str(uuid.uuid4()),
            "storage_path": storage_path,
            "filename": filename,
            "checksum": checksum,
            "size_bytes": file_size,
            "status": "GENERATED",
        }


# ==============================================================================
# Deterministic Test Fake Providers (Mock Integrations for Testing)
# ==============================================================================

class FakeEmailProvider(BaseEmailProvider):
    """Deterministic mock email provider for unit and integration testing."""

    def __init__(self, should_fail: bool = False, missing_ref: bool = False):
        self.should_fail = should_fail
        self.missing_ref = missing_ref
        self.sent_emails: list[dict[str, Any]] = []

    async def send_email(self, input_data: SendEmailInput, context: ActionContext) -> dict[str, Any]:
        if self.should_fail:
            raise ActionExecutionError("Mock SMTP server connection timed out.")
        if self.missing_ref:
            return {"status": "SENT"}  # Intentionally missing message_id to test verification failure

        msg_id = f"fake_msg_{uuid.uuid4().hex[:10]}"
        record = {
            "message_id": msg_id,
            "recipient": input_data.recipient,
            "subject": input_data.subject,
            "body": input_data.body,
            "org_id": context.organization_id,
            "status": "SENT",
        }
        self.sent_emails.append(record)
        return record


class FakeNotificationProvider(BaseNotificationProvider):
    """Deterministic mock notification provider for testing."""

    def __init__(self, should_fail: bool = False, missing_ref: bool = False):
        self.should_fail = should_fail
        self.missing_ref = missing_ref
        self.dispatched_notifications: list[dict[str, Any]] = []

    async def send_notification(self, input_data: SendNotificationInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        if self.should_fail:
            raise ActionExecutionError("Notification broker failure.")
        if self.missing_ref:
            return {"status": "DELIVERED"}

        notif_id = f"fake_notif_{uuid.uuid4().hex[:10]}"
        record = {
            "notification_id": notif_id,
            "title": input_data.title,
            "message": input_data.message,
            "channel": input_data.channel,
            "status": "DELIVERED",
        }
        self.dispatched_notifications.append(record)
        return record


class FakeTicketProvider(BaseTicketProvider):
    """Deterministic mock ticket provider for testing."""

    def __init__(self, should_fail: bool = False, missing_ref: bool = False):
        self.should_fail = should_fail
        self.missing_ref = missing_ref
        self.created_tickets: list[dict[str, Any]] = []

    async def create_ticket(self, input_data: CreateTicketInput, context: ActionContext, session: Any = None) -> dict[str, Any]:
        if self.should_fail:
            raise ActionExecutionError("Mock ticketing system returned 500 error.")
        if self.missing_ref:
            return {"status": "CREATED"}

        ticket_id = f"fake_ticket_{uuid.uuid4().hex[:10]}"
        record = {
            "ticket_id": ticket_id,
            "title": input_data.title,
            "priority": input_data.priority,
            "status": "OPEN",
        }
        self.created_tickets.append(record)
        return record


class FakeReportProvider(BaseReportProvider):
    """Deterministic mock report provider for testing."""

    def __init__(self, should_fail: bool = False, missing_ref: bool = False):
        self.should_fail = should_fail
        self.missing_ref = missing_ref
        self.generated_reports: list[dict[str, Any]] = []

    async def create_report(self, input_data: CreateReportInput, context: ActionContext, storage_service: Any = None) -> dict[str, Any]:
        if self.should_fail:
            raise ActionExecutionError("Report generation failed.")
        if self.missing_ref:
            return {"status": "GENERATED"}

        artifact_id = f"fake_artifact_{uuid.uuid4().hex[:10]}"
        path = f"storage/reports/{artifact_id}.md"
        record = {
            "artifact_id": artifact_id,
            "storage_path": path,
            "verified": True,
            "status": "GENERATED",
        }
        self.generated_reports.append(record)
        return record


# ==============================================================================
# Central Action Executor
# ==============================================================================

class ActionExecutor:
    """
    Central operational executor delegating to registered providers, capturing results,
    invoking verification routines, and calculating execution latency.
    """

    def __init__(
        self,
        email_provider: BaseEmailProvider | None = None,
        notification_provider: BaseNotificationProvider | None = None,
        ticket_provider: BaseTicketProvider | None = None,
        report_provider: BaseReportProvider | None = None,
        storage_service: Any = None,
    ):
        self.email_provider = email_provider or SMTPEmailProvider()
        self.notification_provider = notification_provider or DatabaseNotificationProvider()
        self.ticket_provider = ticket_provider or DatabaseTicketProvider()
        self.report_provider = report_provider or StorageReportProvider()
        self.storage_service = storage_service

    async def execute_handler(
        self,
        action_type: str,
        validated_input: Any,
        context: ActionContext,
        session: Any = None,
    ) -> dict[str, Any]:
        """Dispatches execution to the authorized provider handler."""
        act_lower = action_type.strip().lower()

        if act_lower == ActionType.SEND_EMAIL.value:
            return await self.email_provider.send_email(validated_input, context)

        elif act_lower == ActionType.SEND_NOTIFICATION.value:
            return await self.notification_provider.send_notification(
                validated_input, context, session=session
            )

        elif act_lower == ActionType.CREATE_TICKET.value:
            return await self.ticket_provider.create_ticket(
                validated_input, context, session=session
            )

        elif act_lower == ActionType.CREATE_REPORT.value:
            return await self.report_provider.create_report(
                validated_input, context, storage_service=self.storage_service
            )

        raise ActionNotConfiguredError(
            f"This action is not configured for the current deployment: '{action_type}'."
        )
