import os
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Optional


@dataclass
class SMTPSettings:
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    use_tls: bool
    use_ssl: bool
    sender: str


def load_smtp_settings() -> SMTPSettings:
    host = os.getenv("SMTP_HOST", "localhost")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    sender = os.getenv("EMAIL_SENDER", username or "no-reply@example.com")
    return SMTPSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        use_tls=use_tls,
        use_ssl=use_ssl,
        sender=sender,
    )


def send_email(recipient: str, subject: str, body: str, settings: SMTPSettings) -> None:
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = settings.sender
    message["To"] = recipient

    if settings.use_ssl:
        server = smtplib.SMTP_SSL(settings.host, settings.port)
    else:
        server = smtplib.SMTP(settings.host, settings.port)

    try:
        server.ehlo()
        if settings.use_tls and not settings.use_ssl:
            server.starttls()
            server.ehlo()
        if settings.username and settings.password:
            server.login(settings.username, settings.password)
        server.sendmail(settings.sender, [recipient], message.as_string())
    finally:
        server.quit()
