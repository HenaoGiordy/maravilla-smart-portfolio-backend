from email.message import EmailMessage
import socket
import smtplib

from app.config.settings import Settings


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @staticmethod
    def _resolve_connection_host(host: str, port: int) -> str:
        try:
            addresses = socket.getaddrinfo(host, port, family=socket.AF_INET, type=socket.SOCK_STREAM)
        except socket.gaierror:
            return host

        if not addresses:
            return host

        return str(addresses[0][4][0])

    def send_email(self, recipient_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        host = self._settings.smtp_host.strip() if self._settings.smtp_host else None
        sender = self._settings.smtp_sender_email.strip() if self._settings.smtp_sender_email else None
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
        username = self._settings.smtp_username.strip() if self._settings.smtp_username else None
        password = self._settings.smtp_password.strip() if self._settings.smtp_password else None
        timeout_seconds = max(3, int(getattr(self._settings, "smtp_timeout_seconds", 10)))

        if "gmail.com" in host.lower() and (not username or not password):
            raise ValueError("Gmail SMTP requires SMTP_USERNAME and SMTP_PASSWORD (App Password)")

        if "gmail.com" in host.lower() and password:
            password = password.replace(" ", "")

        connection_host = self._resolve_connection_host(host, port)

        with smtplib.SMTP(timeout=timeout_seconds) as smtp:
            smtp.connect(connection_host, port)
            smtp._host = host
            if self._settings.smtp_use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
