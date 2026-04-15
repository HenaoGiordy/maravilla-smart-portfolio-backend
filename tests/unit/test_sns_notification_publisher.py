from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
import asyncio

import pytest

from app.domain.entities.notification import NotificationEvent
from app.infrastructure.external import sns_notification_publisher as sns_module
from app.infrastructure.external.sns_notification_publisher import SnsNotificationPublisher


def _build_event() -> NotificationEvent:
    return NotificationEvent(
        event_id="evt-123",
        event_type="variable_income_update",
        occurred_at=datetime.now(UTC),
        user_id=77,
        email="user@example.com",
        metadata={"category": "Renta Variable"},
    )


@pytest.mark.asyncio
async def test_publish_returns_when_notifications_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        notifications_enabled=False,
        aws_sns_topic_arn="arn:aws:sns:us-east-1:123456789012:topic",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
    )
    publisher = SnsNotificationPublisher(settings=settings)

    def fail_build_client():
        raise AssertionError("_build_client should not be called when disabled")

    monkeypatch.setattr(
        publisher,
        "_build_client",
        fail_build_client,
    )

    await publisher.publish(_build_event())


@pytest.mark.asyncio
async def test_publish_raises_without_topic_arn() -> None:
    settings = SimpleNamespace(
        notifications_enabled=True,
        aws_sns_topic_arn=None,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
    )
    publisher = SnsNotificationPublisher(settings=settings)

    with pytest.raises(ValueError, match="AWS SNS topic ARN is required"):
        await publisher.publish(_build_event())


@pytest.mark.asyncio
async def test_publish_calls_sns_with_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        notifications_enabled=True,
        aws_sns_topic_arn="arn:aws:sns:us-east-1:123456789012:topic",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_region=None,
    )
    publisher = SnsNotificationPublisher(settings=settings)

    mock_client = MagicMock()
    monkeypatch.setattr(publisher, "_build_client", lambda: mock_client)

    async def fake_to_thread(function, *args, **kwargs):
        await asyncio.sleep(0)
        function(*args, **kwargs)

    monkeypatch.setattr(sns_module.asyncio, "to_thread", fake_to_thread)

    event = _build_event()
    await publisher.publish(event)

    assert mock_client.publish.call_count == 1
    kwargs = mock_client.publish.call_args.kwargs
    assert kwargs["TopicArn"] == settings.aws_sns_topic_arn
    assert kwargs["Subject"] == f"event:{event.event_type}"
    assert kwargs["MessageAttributes"]["user_id"]["StringValue"] == str(event.user_id)
