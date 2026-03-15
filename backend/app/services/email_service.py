"""Swappable email service interface with a mock implementation."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol

from app.models.alert import MockEmailMessage
from app.services.state_store import JsonStateStore

logger = logging.getLogger(__name__)

DASHBOARD_URL = "http://localhost:3000"

_SCORE_BAND_COLOR = {
    "Normal": "#2f7a52",
    "Elevated": "#c8891a",
    "High": "#c8891a",
    "Sustained Overload Risk": "#b34236",
}

_EMAIL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4efe6;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4efe6;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
  style="background:#ffffff;border-radius:24px;overflow:hidden;
         box-shadow:0 20px 60px rgba(72,44,26,0.14);max-width:600px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#9e2d22 0%,#c75a2d 100%);padding:32px 40px 28px;">
      <p style="margin:0;color:rgba(255,255,255,0.65);font-size:11px;
                letter-spacing:0.18em;text-transform:uppercase;font-weight:600;">
        MindScope &nbsp;·&nbsp; Cognitive Load Monitor
      </p>
      <h1 style="margin:10px 0 0;color:#ffffff;font-size:30px;font-weight:800;letter-spacing:-0.5px;">
        ⚠️&nbsp; Overload Alert
      </h1>
    </td>
  </tr>

  <!-- SCORE ROW -->
  <tr>
    <td style="padding:32px 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="vertical-align:middle;">
            <p style="margin:0 0 4px;font-size:11px;color:#6c5a4f;
                      text-transform:uppercase;letter-spacing:0.12em;font-weight:600;">
              Overload Score
            </p>
            <p style="margin:0;font-size:80px;font-weight:800;
                      color:{score_color};line-height:1;letter-spacing:-3px;">
              {score}
            </p>
            <span style="display:inline-block;background:{score_color};color:#fff;
                         border-radius:999px;padding:5px 16px;font-size:13px;
                         font-weight:700;margin-top:8px;">
              {band}
            </span>
          </td>
          <td style="vertical-align:top;text-align:right;padding-left:16px;">
            <div style="background:rgba(179,66,54,0.07);border:1px solid rgba(179,66,54,0.2);
                        border-radius:16px;padding:18px 20px;display:inline-block;text-align:center;">
              <p style="margin:0 0 6px;font-size:11px;color:#6c5a4f;text-transform:uppercase;
                        letter-spacing:0.1em;">Rule triggered</p>
              <p style="margin:0;font-size:15px;font-weight:700;color:#b34236;
                        font-family:monospace;">{rule}</p>
            </div>
            <div style="margin-top:12px;background:rgba(47,122,82,0.07);
                        border:1px solid rgba(47,122,82,0.2);border-radius:16px;
                        padding:14px 20px;display:inline-block;text-align:center;">
              <p style="margin:0 0 4px;font-size:11px;color:#6c5a4f;text-transform:uppercase;
                        letter-spacing:0.1em;">Time detected</p>
              <p style="margin:0;font-size:13px;font-weight:600;color:#21160f;">{sent_at}</p>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- BODY TEXT -->
  <tr>
    <td style="padding:22px 40px 0;">
      <p style="margin:0;font-size:16px;color:#21160f;line-height:1.65;">
        <strong>{user_id}'s</strong> cognitive load has stayed elevated across multiple
        consecutive windows, crossing the <strong style="color:#b34236;">{rule}</strong>
        persistence threshold. This is a sustained pattern — not a one-off spike.
      </p>
    </td>
  </tr>

  <!-- CTA BUTTONS -->
  <tr>
    <td style="padding:26px 40px 0;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <a href="{dashboard_url}"
               style="display:inline-block;background:#c75a2d;color:#ffffff;
                      text-decoration:none;padding:14px 28px;border-radius:12px;
                      font-weight:700;font-size:15px;letter-spacing:0.01em;">
              View Live Dashboard &rarr;
            </a>
          </td>
          <td style="padding-left:12px;">
            <a href="{dashboard_url}?tab=copilot"
               style="display:inline-block;background:rgba(199,90,45,0.09);
                      color:#c75a2d;border:1.5px solid rgba(199,90,45,0.3);
                      text-decoration:none;padding:14px 28px;border-radius:12px;
                      font-weight:700;font-size:15px;">
              🧠 Prioritize My Tasks
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- WHAT TO DO -->
  <tr>
    <td style="padding:26px 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#fdf7ee;border-radius:16px;border:1px solid rgba(94,65,39,0.12);">
        <tr>
          <td style="padding:20px 24px;">
            <p style="margin:0 0 14px;font-weight:700;font-size:15px;color:#21160f;">
              What you can do right now
            </p>
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="padding:7px 0;color:#6c5a4f;font-size:14px;line-height:1.5;">
                  🧘&nbsp; <strong>Take a 5-minute break</strong> — step away from the screen
                </td>
              </tr>
              <tr>
                <td style="padding:7px 0;color:#6c5a4f;font-size:14px;line-height:1.5;">
                  📋&nbsp; <strong>Open Task Copilot</strong> — brain-dump and let AI reprioritize
                </td>
              </tr>
              <tr>
                <td style="padding:7px 0;color:#6c5a4f;font-size:14px;line-height:1.5;">
                  🔕&nbsp; <strong>Close non-essential tabs</strong> — reduce fragmentation
                </td>
              </tr>
              <tr>
                <td style="padding:7px 0;color:#6c5a4f;font-size:14px;line-height:1.5;">
                  🍕&nbsp; <strong>Haven't eaten?</strong> Order via Uber Eats so you don't have to think about it
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- DIVIDER + FOOTER -->
  <tr>
    <td style="padding:26px 40px 32px;">
      <hr style="border:none;border-top:1px solid rgba(94,65,39,0.1);margin:0 0 20px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <p style="margin:0;font-size:12px;color:#a09080;line-height:1.6;">
              <strong style="color:#6c5a4f;">MindScope</strong> &nbsp;·&nbsp;
              Cognitive Load Monitor &nbsp;·&nbsp; Hackathon Demo<br>
              This alert fires only after sustained overload — not on isolated spikes.<br>
              <a href="{dashboard_url}" style="color:#c75a2d;text-decoration:none;">
                Open dashboard
              </a>
              &nbsp;&middot;&nbsp;
              <a href="{dashboard_url}?tab=copilot" style="color:#c75a2d;text-decoration:none;">
                Task Copilot
              </a>
            </p>
          </td>
          <td align="right" style="vertical-align:bottom;">
            <p style="margin:0;font-size:28px;">🧠</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


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
        if overload_score >= 85:
            band = "Sustained Overload Risk"
        elif overload_score >= 75:
            band = "High"
        elif overload_score >= 60:
            band = "Elevated"
        else:
            band = "Normal"
        score_color = _SCORE_BAND_COLOR.get(band, "#b34236")
        html_body = _EMAIL_HTML.format(
            score=round(overload_score),
            band=band,
            score_color=score_color,
            rule=rule or "persistence_rule",
            user_id=user_id,
            sent_at=sent_at.strftime("%B %d, %Y at %H:%M UTC"),
            dashboard_url=DASHBOARD_URL,
        )
        message = MockEmailMessage(
            recipient=self.default_recipient,
            subject=f"[MindScope] ⚠️ Overload alert for {user_id} — score {round(overload_score)}",
            body=html_body,
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
        """Send an actual SMTP email with HTML body and persist a local record."""

        message = super().send_alert(user_id=user_id, overload_score=overload_score, rule=rule)
        mime = MIMEMultipart("alternative")
        mime["From"] = self.smtp_from_email
        mime["To"] = message.recipient
        mime["Subject"] = message.subject
        plain_text = (
            f"MindScope Overload Alert\n\n"
            f"User {user_id} crossed the '{rule}' persistence rule "
            f"with a score of {overload_score:.0f}.\n\n"
            f"Open your dashboard: {DASHBOARD_URL}\n"
            f"Prioritize tasks: {DASHBOARD_URL}?tab=copilot\n"
        )
        mime.attach(MIMEText(plain_text, "plain"))
        mime.attach(MIMEText(message.body, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as client:
                if self.smtp_use_tls:
                    client.starttls()
                if self.smtp_username:
                    client.login(self.smtp_username, self.smtp_password)
                client.sendmail(self.smtp_from_email, message.recipient, mime.as_string())
            logger.info("HTML alert email sent to %s", message.recipient)
        except Exception as exc:  # noqa: BLE001
            logger.error("SMTP send failed (alert still logged): %s", exc)
        return message
