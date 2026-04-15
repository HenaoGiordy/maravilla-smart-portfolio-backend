from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.infrastructure.external import smtp_email_sender as smtp_module
from app.infrastructure.external.smtp_email_sender import SmtpEmailSender


def _settings(**overrides):
    defaults = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": None,
        "smtp_password": None,
        "smtp_use_tls": True,
        "smtp_sender_email": "no-reply@example.com",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_send_email_requires_host_and_sender() -> None:
    sender = SmtpEmailSender(settings=_settings(smtp_host=None))
    with pytest.raises(ValueError, match="SMTP host and SMTP sender email are required"):
        sender.send_email("dest@example.com", "subject", "body")


def test_send_email_uses_tls_login_and_send(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = SmtpEmailSender(settings=_settings())

    smtp_mock = MagicMock()

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __enter__(self):
            return smtp_mock

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(smtp_module.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(sender, "_resolve_connection_host", lambda host, port: "127.0.0.1")

    sender.send_email("dest@example.com", "subject", "body", "<p>body</p>")

    smtp_mock.connect.assert_called_once_with("127.0.0.1", 587)
    smtp_mock.starttls.assert_called_once()
    smtp_mock.login.assert_not_called()
    smtp_mock.send_message.assert_called_once()


def test_resolve_connection_host_prefers_ipv4(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        smtp_module.socket,
        "getaddrinfo",
        lambda host, port, family, type: [
            (smtp_module.socket.AF_INET, smtp_module.socket.SOCK_STREAM, 6, "", ("74.125.132.108", port))
        ],
    )

    resolved = SmtpEmailSender._resolve_connection_host("smtp.gmail.com", 587)

    assert resolved == "74.125.132.108"
