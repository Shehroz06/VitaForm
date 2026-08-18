import logging
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Annotated, Protocol

import aiosmtplib
from fastapi import Depends

from app.config.settings import Settings, get_settings

logger = logging.getLogger("app.email")


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Dev-only sender that logs instead of delivering. Active when
    EMAIL_PROVIDER=console (the default) -- no SMTP credentials required."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, body)


class SMTPEmailSender:
    """Real delivery over SMTP. Works with any standard SMTP endpoint --
    a relay, or the SMTP interface of a transactional provider (SendGrid,
    Mailgun, SES, Resend, Postmark, etc.) -- so switching providers is a
    credentials change (SMTP_HOST/PORT/USERNAME/PASSWORD), never a code
    change, matching this project's provider-independence principle."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        from_address: str,
        from_name: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._from_address = from_address
        self._from_name = from_name

    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = f"{self._from_name} <{self._from_address}>"
        message["To"] = to
        message["Subject"] = subject
        # A missing Date/Message-ID is a common spam-filter signal --
        # EmailMessage doesn't set either automatically, only smtplib's
        # legacy sendmail() does that implicitly.
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=self._from_address.split("@")[-1])
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            start_tls=self._use_tls,
        )


# Known-provider host shorthands: EMAIL_PROVIDER=gmail only needs
# SMTP_USERNAME (the Gmail address) and SMTP_PASSWORD (a 16-character Gmail
# *app password*, not the account password -- generate one at
# https://myaccount.google.com/apppasswords, requires 2-Step Verification
# enabled). Port/TLS already default to 587/STARTTLS, which is what Gmail
# expects, so nothing else needs configuring.
_PROVIDER_HOSTS = {"gmail": "smtp.gmail.com"}


def get_email_sender(settings: Annotated[Settings, Depends(get_settings)]) -> EmailSender:
    if settings.email_provider in ("smtp", *_PROVIDER_HOSTS):
        host = settings.smtp_host or _PROVIDER_HOSTS.get(settings.email_provider)
        if not host:
            raise ValueError("SMTP_HOST is required when EMAIL_PROVIDER=smtp.")
        if not settings.smtp_username or not settings.smtp_password:
            raise ValueError(
                f"SMTP_USERNAME and SMTP_PASSWORD are required when "
                f"EMAIL_PROVIDER={settings.email_provider}."
            )
        return SMTPEmailSender(
            host=host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            # Gmail rejects a From address that doesn't match (or isn't a
            # verified alias of) the authenticated account, so default to
            # the login itself unless a from-address was explicitly set.
            from_address=(
                settings.smtp_from_address
                if settings.smtp_from_address != "no-reply@example.com"
                else settings.smtp_username
            ),
            from_name=settings.smtp_from_name,
        )
    return ConsoleEmailSender()
