import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.infrastructure.external.sqs_notification_consumer import SqsNotificationConsumer


def _settings(enabled: bool = True):
    return SimpleNamespace(
        notifications_enabled=enabled,
        aws_sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/test",
        aws_sqs_max_messages=10,
        aws_sqs_wait_time_seconds=1,
        aws_sqs_visibility_timeout_seconds=30,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
        aws_ses_sender_email="no-reply@example.com",
        aws_ses_configuration_set=None,
        notifications_email_subject_prefix="[Maravilla]",
    )


def test_extract_event_from_sns_envelope() -> None:
    consumer = SqsNotificationConsumer(settings=_settings())
    envelope = {
        "Type": "Notification",
        "Message": json.dumps({"event_type": "x", "user_id": 1, "email": "a@b.com", "event_id": "e", "occurred_at": "2026-01-01T00:00:00Z"}),
    }

    event = consumer._extract_event(json.dumps(envelope))

    assert event["event_type"] == "x"
    assert event["user_id"] == 1


def test_poll_once_returns_zero_when_disabled() -> None:
    consumer = SqsNotificationConsumer(settings=_settings(enabled=False))
    assert consumer.poll_once() == 0


def test_poll_once_processes_and_deletes_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    consumer = SqsNotificationConsumer(settings=_settings())

    mock_client = MagicMock()
    mock_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": "r1",
                "Body": json.dumps({"event_type": "x", "user_id": 1, "email": "a@b.com", "event_id": "e", "occurred_at": "2026-01-01T00:00:00Z"}),
            }
        ]
    }
    monkeypatch.setattr(consumer, "_build_client", lambda: mock_client)

    processed_events: list[dict] = []
    monkeypatch.setattr(consumer, "_process_event", lambda event: processed_events.append(event))

    processed_count = consumer.poll_once()

    assert processed_count == 1
    assert len(processed_events) == 1
    assert mock_client.delete_message.call_count == 1


def test_poll_once_keeps_message_when_processing_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    consumer = SqsNotificationConsumer(settings=_settings())

    mock_client = MagicMock()
    mock_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": "r1",
                "Body": json.dumps({"event_type": "x", "user_id": 1, "email": "a@b.com", "event_id": "e", "occurred_at": "2026-01-01T00:00:00Z"}),
            }
        ]
    }
    monkeypatch.setattr(consumer, "_build_client", lambda: mock_client)

    def failing_process(_event: dict) -> None:
        raise RuntimeError("processing error")

    monkeypatch.setattr(consumer, "_process_event", failing_process)

    processed_count = consumer.poll_once()

    assert processed_count == 1
    mock_client.delete_message.assert_not_called()
