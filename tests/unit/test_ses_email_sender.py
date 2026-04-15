from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.infrastructure.external.ses_email_sender import SesEmailSender


def test_send_email_raises_when_sender_not_configured() -> None:
    settings = SimpleNamespace(
        aws_ses_sender_email=None,
        aws_ses_configuration_set=None,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
    )
    sender = SesEmailSender(settings=settings)

    with pytest.raises(ValueError, match="AWS SES sender email is required"):
        sender.send_email("dest@example.com", "Subject", "Body")


def test_send_email_builds_payload_with_html_and_configuration_set(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        aws_ses_sender_email="no-reply@example.com",
        aws_ses_configuration_set="config-set",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
    )
    sender = SesEmailSender(settings=settings)

    mock_client = MagicMock()
    monkeypatch.setattr(sender, "_build_client", lambda: mock_client)

    sender.send_email(
        recipient_email="dest@example.com",
        subject="Test subject",
        text_body="Text body",
        html_body="<p>HTML body</p>",
    )

    assert mock_client.send_email.call_count == 1
    payload = mock_client.send_email.call_args.kwargs
    assert payload["Source"] == "no-reply@example.com"
    assert payload["Destination"]["ToAddresses"] == ["dest@example.com"]
    assert payload["Message"]["Subject"]["Data"] == "Test subject"
    assert payload["Message"]["Body"]["Text"]["Data"] == "Text body"
    assert payload["Message"]["Body"]["Html"]["Data"] == "<p>HTML body</p>"
    assert payload["ConfigurationSetName"] == "config-set"
