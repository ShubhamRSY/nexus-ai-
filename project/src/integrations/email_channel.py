"""Email channel — SMTP outbound and inbound webhook processing."""

from __future__ import annotations

import smtplib
import uuid
from email.message import EmailMessage

import structlog

from src.config import get_settings
from src.database import db
from src.request_context import set_request_context

logger = structlog.get_logger()


class EmailChannel:
    def _configured(self) -> bool:
        s = get_settings()
        return bool(s.smtp_host and s.smtp_from_email)

    async def send_email(self, to: str, subject: str, body: str, session_id: str = "", tenant_id: str = "default") -> dict:
        settings = get_settings()
        sid = session_id or f"email-{uuid.uuid4().hex[:12]}"

        if not self._configured():
            logger.info("email_mock_send", to=to, subject=subject)
            db.save_email_message(sid, tenant_id, to, settings.smtp_from_email or "noreply@nexus.local", subject, body, "outbound")
            return {"status": "mock_sent", "session_id": sid, "to": to, "subject": subject}

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to
        msg.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_user:
                    smtp.starttls()
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        except Exception as exc:
            logger.error("email_send_failed", error=str(exc))
            return {"status": "failed", "error": str(exc)}

        db.save_email_message(sid, tenant_id, to, settings.smtp_from_email, subject, body, "outbound")
        existing = db.get_session(sid)
        if not existing:
            db.create_session(sid, tenant_id, "chat_support", "email", to)
        db.save_message(sid, "assistant", body)
        logger.info("email_sent", session_id=sid, to=to)
        return {"status": "sent", "session_id": sid, "to": to, "subject": subject}

    async def handle_inbound(self, payload: dict, tenant_id: str = "default") -> dict:
        """Process inbound email webhook (SendGrid/Mailgun-style JSON)."""
        from src.api.deps import get_session as get_orch_session
        from src.integrations.translation import detect_locale, localize_response, translate_text

        sender = payload.get("from") or payload.get("sender") or ""
        subject = payload.get("subject", "(no subject)")
        body = payload.get("text") or payload.get("body") or payload.get("html", "")
        if isinstance(body, list):
            body = "\n".join(str(x) for x in body)

        sid = payload.get("session_id") or f"email-{uuid.uuid4().hex[:12]}"
        locale = detect_locale(f"{subject}\n{body}")

        if not db.get_session(sid):
            db.create_session(sid, tenant_id, "chat_support", "email", sender)
        db.update_session_locale(sid, locale)
        db.save_email_message(sid, tenant_id, sender, payload.get("to", ""), subject, body, "inbound")

        user_text = f"Subject: {subject}\n\n{body}"
        translated = await translate_text(user_text, target_locale="en", source_locale=locale)
        inbound_text = translated["text"]

        set_request_context(session_id=sid, tenant_id=tenant_id)
        orch = get_orch_session(sid, "chat_support", tenant_id)
        result = await orch.invoke(user_input=inbound_text, customer_info=sender or "email customer")
        db.save_message(sid, "user", user_text)
        db.save_message(sid, "assistant", result["response"], tool_calls=result.get("tool_calls", []))

        session = db.get_session(sid) or {}
        reply_body = result["response"]
        if session.get("handoff_status") == "queued":
            reply_body = "Thank you for your email. A specialist will respond shortly."
        else:
            reply_body = await localize_response(reply_body, locale)

        auto_reply = None
        if sender and self._configured():
            auto_reply = await self.send_email(
                to=sender,
                subject=f"Re: {subject}",
                body=reply_body,
                session_id=sid,
                tenant_id=tenant_id,
            )

        return {
            "session_id": sid,
            "from": sender,
            "subject": subject,
            "response": reply_body,
            "locale": locale,
            "auto_reply": auto_reply,
        }


email_channel = EmailChannel()
