"""Swappable email service interface with a mock implementation."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Protocol

from app.models.alert import MockEmailMessage
from app.services.state_store import JsonStateStore

logger = logging.getLogger(__name__)


class EmailService(Protocol):
    """Small interface that can later be swapped for SMTP, Resend, or SES."""

    def send_alert(self, user_id: str, overload_score: float, rule: str) -> MockEmailMessage:
        """Send an overload-risk alert for a user."""


class MockEmailService:
    """In-memory fake email sender used during the hackathon MVP stage."""

    def __init__(self, default_recipient: str, store: JsonStateStore | None = None) -> None:
        self.default_recipient = default_recipient
        self.store = store
        self._messages: list[MockEmailMessage] = self._load_messages()

    def _load_messages(self) -> list[MockEmailMessage]:
        """Hydrate persisted mock messages when available."""

        if self.store is None:
            return []
        raw = self.store.load(default=[])
        messages: list[MockEmailMessage] = []
        for item in raw:
            try:
                messages.append(MockEmailMessage.model_validate(item))
            except Exception:
                continue
        return messages

    def _persist(self) -> None:
        """Write current message list to disk."""

        if self.store is None:
            return
        self.store.save([message.model_dump(mode="json") for message in self._messages])

    def send_alert(self, user_id: str, overload_score: float, rule: str) -> MockEmailMessage:
        """Store a mock email message instead of sending a real one."""

        sent_at = datetime.now(timezone.utc)
        message = MockEmailMessage(
            recipient=self.default_recipient,
            subject=f"[MindScope] Elevated overload risk for {user_id}",
            body=(
                f"User {user_id} crossed the overload persistence rule '{rule}' "
                f"with a score of {overload_score:.2f}."
            ),
            sent_at=sent_at,
        )
        self._messages.append(message)
        self._persist()
        return message

    def list_messages(self) -> list[MockEmailMessage]:
        """Return stored mock emails for debugging and demos."""

        return list(self._messages)


class SMTPEmailService(MockEmailService):
    """SMTP-backed implementation that still keeps a local sent-message log."""

    def __init__(
        self,
        *,
        default_recipient: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        smtp_use_tls: bool,
        smtp_from_email: str,
        store: JsonStateStore | None = None,
    ) -> None:
        super().__init__(default_recipient=default_recipient, store=store)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.smtp_from_email = smtp_from_email

    def send_alert(self, user_id: str, overload_score: float, rule: str) -> MockEmailMessage:
        """Send an actual SMTP email and persist a local record."""

        message = super().send_alert(user_id=user_id, overload_score=overload_score, rule=rule)
        email = EmailMessage()
        email["From"] = self.smtp_from_email
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email.set_content(message.body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as client:
                if self.smtp_use_tls:
                    client.starttls()
                if self.smtp_username:
                    client.login(self.smtp_username, self.smtp_password)
                client.send_message(email)
            logger.info("Alert email sent to %s", message.recipient)
        except Exception as exc:  # noqa: BLE001
            logger.error("SMTP send failed (alert still logged): %s", exc)
        return message
