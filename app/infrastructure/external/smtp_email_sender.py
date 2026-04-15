from email.message import EmailMessage
import smtplib

from app.config.settings import Settings


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_email(self, recipient_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        host = self._settings.smtp_host
        sender = self._settings.smtp_sender_email
        if not host or not sender:
            raise ValueError("SMTP host and SMTP sender email are required for SMTP delivery")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient_email
        message.set_content(text_body)

        if html_body:
            message.add_alternative(html_body, subtype="html")

        port = self._settings.smtp_port
        username = self._settings.smtp_username
        password = self._settings.smtp_password
        timeout_seconds = max(3, int(getattr(self._settings, "smtp_timeout_seconds", 10)))

        if "gmail.com" in host.lower() and (not username or not password):
            raise ValueError("Gmail SMTP requires SMTP_USERNAME and SMTP_PASSWORD (App Password)")

        with smtplib.SMTP(host, port, timeout=timeout_seconds) as smtp:
            if self._settings.smtp_use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
