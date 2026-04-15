from datetime import UTC, datetime

from app.application.use_cases.notification_email_service import NotificationEmailService
from app.domain.entities.notification import NotificationEvent


class DummyEmailSender:
    def __init__(self) -> None:
        self.calls = []

    def send_email(self, recipient_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        self.calls.append(
            {
                "recipient_email": recipient_email,
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
            }
        )


class DummySettings:
    notifications_email_subject_prefix = "[Maravilla]"


def test_notification_email_service_user_registered_template() -> None:
    sender = DummyEmailSender()
    service = NotificationEmailService(settings=DummySettings(), email_sender=sender)

    event = NotificationEvent(
        event_id="evt-1",
        event_type="user_registered",
        occurred_at=datetime.now(UTC),
        user_id=10,
        email="investor@example.com",
        metadata={"name": "Ana"},
    )

    service.send_event_email(event)

    assert len(sender.calls) == 1
    payload = sender.calls[0]
    assert payload["recipient_email"] == "investor@example.com"
    assert payload["subject"] == "[Maravilla] Bienvenida a Maravilla"
    assert "Hola Ana" in payload["text_body"]


def test_notification_email_service_profile_assigned_template() -> None:
    sender = DummyEmailSender()
    service = NotificationEmailService(settings=DummySettings(), email_sender=sender)

    event = NotificationEvent(
        event_id="evt-2",
        event_type="profile_assigned",
        occurred_at=datetime.now(UTC),
        user_id=22,
        email="user22@example.com",
        metadata={"profile_name": "Moderado", "risk_level": "medium"},
    )

    service.send_event_email(event)

    assert len(sender.calls) == 1
    payload = sender.calls[0]
    assert payload["subject"] == "[Maravilla] Perfil de inversión asignado"
    assert "Perfil: Moderado" in payload["text_body"]
    assert "Riesgo: medium" in payload["text_body"]
