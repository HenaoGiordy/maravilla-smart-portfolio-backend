import json
import logging
import time
from typing import Any

import boto3

from app.application.use_cases.notification_email_service import NotificationEmailService
from app.config.settings import Settings
from app.domain.entities.notification import NotificationEvent
from app.infrastructure.external.ses_email_sender import SesEmailSender
from app.infrastructure.external.smtp_email_sender import SmtpEmailSender

logger = logging.getLogger(__name__)


class SqsNotificationConsumer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sqs_client = None
        email_provider = str(getattr(settings, "email_provider", "smtp")).lower()
        if email_provider == "ses":
            email_sender = SesEmailSender(settings=settings)
        else:
            email_sender = SmtpEmailSender(settings=settings)
        self._email_service = NotificationEmailService(settings=settings, email_sender=email_sender)

    def _build_client(self):
        if self._sqs_client is not None:
            return self._sqs_client

        session_params: dict[str, Any] = {}
        if self._settings.aws_access_key_id:
            session_params["aws_access_key_id"] = self._settings.aws_access_key_id
        if self._settings.aws_secret_access_key:
            session_params["aws_secret_access_key"] = self._settings.aws_secret_access_key
        if self._settings.aws_region:
            session_params["region_name"] = self._settings.aws_region

        session = boto3.session.Session(**session_params)
        self._sqs_client = session.client("sqs")
        return self._sqs_client

    def _extract_event(self, raw_body: str) -> dict[str, Any]:
        body = json.loads(raw_body)
        if isinstance(body, dict) and body.get("Type") == "Notification" and "Message" in body:
            nested = body.get("Message")
            if isinstance(nested, str):
                return json.loads(nested)
            if isinstance(nested, dict):
                return nested
        if isinstance(body, dict):
            return body
        raise ValueError("Invalid notification payload")

    def _process_event(self, event: dict[str, Any]) -> None:
        notification_event = NotificationEvent.model_validate(event)
        event_type = notification_event.event_type
        email = notification_event.email
        user_id = notification_event.user_id
        logger.info(
            "Notification event received: type=%s user_id=%s email=%s",
            event_type,
            user_id,
            email,
        )
        self._email_service.send_event_email(notification_event)
        logger.info("Notification email sent: event_type=%s user_id=%s", event_type, user_id)

    def poll_once(self) -> int:
        if not self._settings.notifications_enabled:
            return 0

        queue_url = self._settings.aws_sqs_queue_url
        if not queue_url:
            raise ValueError("AWS SQS queue URL is required when notifications are enabled")

        client = self._build_client()
        response = client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=self._settings.aws_sqs_max_messages,
            WaitTimeSeconds=self._settings.aws_sqs_wait_time_seconds,
            VisibilityTimeout=self._settings.aws_sqs_visibility_timeout_seconds,
            MessageAttributeNames=["All"],
        )
        messages = response.get("Messages", [])

        for message in messages:
            receipt_handle = message["ReceiptHandle"]
            try:
                event = self._extract_event(message.get("Body", "{}"))
                self._process_event(event)
                client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            except Exception:
                logger.exception("Error processing SQS notification message")

        return len(messages)

    def run_forever(self, idle_sleep_seconds: float = 1.0) -> None:
        logger.info("SQS notification consumer started")
        while True:
            processed = self.poll_once()
            if processed == 0:
                time.sleep(idle_sleep_seconds)
