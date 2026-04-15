import asyncio
from typing import Any

import boto3

from app.config.settings import Settings
from app.domain.entities.notification import NotificationEvent
from app.domain.ports.notification_publisher import NotificationPublisherPort


class SnsNotificationPublisher(NotificationPublisherPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sns_client = None

    def _is_enabled(self) -> bool:
        return self._settings.notifications_enabled

    def _build_client(self):
        if self._sns_client is not None:
            return self._sns_client

        session_params: dict[str, Any] = {}
        if self._settings.aws_access_key_id:
            session_params["aws_access_key_id"] = self._settings.aws_access_key_id
        if self._settings.aws_secret_access_key:
            session_params["aws_secret_access_key"] = self._settings.aws_secret_access_key
        if self._settings.aws_region:
            session_params["region_name"] = self._settings.aws_region

        session = boto3.session.Session(**session_params)
        self._sns_client = session.client("sns")
        return self._sns_client

    async def publish(self, event: NotificationEvent) -> None:
        if not self._is_enabled():
            return

        topic_arn = self._settings.aws_sns_topic_arn
        if not topic_arn:
            raise ValueError("AWS SNS topic ARN is required when notifications are enabled")

        message = event.model_dump_json()
        client = self._build_client()

        await asyncio.to_thread(
            client.publish,
            TopicArn=topic_arn,
            Message=message,
            Subject=f"event:{event.event_type}",
            MessageAttributes={
                "event_type": {
                    "DataType": "String",
                    "StringValue": event.event_type,
                },
                "user_id": {
                    "DataType": "Number",
                    "StringValue": str(event.user_id),
                },
            },
        )
