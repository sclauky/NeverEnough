from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


async def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    required_settings = {
        "SMTP_HOST": settings.smtp_host,
        "SMTP_USERNAME": settings.smtp_username,
        "SMTP_PASSWORD": settings.smtp_password,
        "SMTP_SENDER": settings.smtp_sender,
    }

    missing_settings = [
        name for name, value in required_settings.items() if not value
    ]

    if missing_settings:
        raise RuntimeError(
            f"Missing email configuration: {', '.join(missing_settings)}"
        )

    message = EmailMessage()
    message["From"] = settings.smtp_sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password.get_secret_value(),
        start_tls=True,
    )