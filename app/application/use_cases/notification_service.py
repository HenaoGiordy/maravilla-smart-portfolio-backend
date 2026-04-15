from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.entities.notification import NotificationEvent
from app.domain.ports.notification_publisher import NotificationPublisherPort


class NotificationService:
    def __init__(self, notification_publisher: NotificationPublisherPort) -> None:
        self.notification_publisher = notification_publisher

    async def publish_event(
        self,
        event_type: str,
        user_id: int,
        email: str,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationEvent:
        event = NotificationEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            metadata=metadata or {},
        )
        await self.notification_publisher.publish(event)
        return event
