from typing import Any

import boto3

from app.config.settings import Settings


class SesEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ses_client = None

    def _build_client(self):
        if self._ses_client is not None:
            return self._ses_client

        session_params: dict[str, Any] = {}
        if self._settings.aws_access_key_id:
            session_params["aws_access_key_id"] = self._settings.aws_access_key_id
        if self._settings.aws_secret_access_key:
            session_params["aws_secret_access_key"] = self._settings.aws_secret_access_key
        if self._settings.aws_region:
            session_params["region_name"] = self._settings.aws_region

        session = boto3.session.Session(**session_params)
        self._ses_client = session.client("ses")
        return self._ses_client

    def send_email(self, recipient_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        sender = self._settings.aws_ses_sender_email
        if not sender:
            raise ValueError("AWS SES sender email is required to send notification emails")

        body: dict[str, Any] = {
            "Text": {"Charset": "UTF-8", "Data": text_body},
        }
        if html_body:
            body["Html"] = {"Charset": "UTF-8", "Data": html_body}

        payload: dict[str, Any] = {
            "Source": sender,
            "Destination": {"ToAddresses": [recipient_email]},
            "Message": {
                "Subject": {"Charset": "UTF-8", "Data": subject},
                "Body": body,
            },
        }

        if self._settings.aws_ses_configuration_set:
            payload["ConfigurationSetName"] = self._settings.aws_ses_configuration_set

        client = self._build_client()
        client.send_email(**payload)
