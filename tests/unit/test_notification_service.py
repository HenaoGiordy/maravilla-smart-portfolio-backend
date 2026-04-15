import asyncio

import pytest

from app.application.use_cases.notification_service import NotificationService


class DummyPublisher:
    def __init__(self) -> None:
        self.events = []

    async def publish(self, event) -> None:
        await asyncio.sleep(0)
        self.events.append(event)


@pytest.mark.asyncio
async def test_notification_service_publishes_event_payload() -> None:
    publisher = DummyPublisher()
    service = NotificationService(notification_publisher=publisher)

    event = await service.publish_event(
        event_type="user_registered",
        user_id=101,
        email="user@example.com",
        metadata={"name": "Test User"},
    )

    assert event.event_type == "user_registered"
    assert event.user_id == 101
    assert event.email == "user@example.com"
    assert event.metadata == {"name": "Test User"}
    assert len(event.event_id) > 0

    assert len(publisher.events) == 1
    assert publisher.events[0].event_id == event.event_id
