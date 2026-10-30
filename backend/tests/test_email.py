import asyncio

from app.core.email import send_email
from app.core.config import settings


async def main():
    await send_email(
        recipient=settings.smtp_username,
        subject="Never Enough - SMTP test",
        body="Your email configuration is working correctly!",
    )
    print("Email sent successfully.")


asyncio.run(main())