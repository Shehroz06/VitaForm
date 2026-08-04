import logging
from typing import Protocol

logger = logging.getLogger("app.email")


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Dev-only sender that logs instead of delivering. Swap for an SMTP/provider
    implementation behind this same interface when going to production."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, body)


def get_email_sender() -> EmailSender:
    return ConsoleEmailSender()
