import pytest

from app.config.settings import Settings
from app.core.email import ConsoleEmailSender, SMTPEmailSender, get_email_sender


def _settings(**overrides: object) -> Settings:
    # _env_file=None: these must be isolated unit tests of get_email_sender's
    # branching logic, never influenced by whatever's actually in the local
    # .env (e.g. real SMTP credentials configured for this dev machine).
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type,call-arg]


def test_console_provider_is_default() -> None:
    sender = get_email_sender(_settings())
    assert isinstance(sender, ConsoleEmailSender)


def test_gmail_provider_resolves_smtp_gmail_host() -> None:
    sender = get_email_sender(
        _settings(
            email_provider="gmail",
            smtp_username="me@gmail.com",
            smtp_password="an-app-password",
        )
    )
    assert isinstance(sender, SMTPEmailSender)
    assert sender._host == "smtp.gmail.com"
    assert sender._port == 587
    # From address defaults to the Gmail login itself, since Gmail rejects
    # a From header that doesn't match the authenticated account.
    assert sender._from_address == "me@gmail.com"


def test_gmail_provider_without_credentials_raises() -> None:
    with pytest.raises(ValueError, match="SMTP_USERNAME"):
        get_email_sender(_settings(email_provider="gmail"))


def test_smtp_provider_without_host_raises() -> None:
    with pytest.raises(ValueError, match="SMTP_HOST"):
        get_email_sender(_settings(email_provider="smtp"))


def test_smtp_provider_respects_explicit_from_address() -> None:
    sender = get_email_sender(
        _settings(
            email_provider="smtp",
            smtp_host="smtp.example.com",
            smtp_username="user",
            smtp_password="pw",
            smtp_from_address="hello@mycompany.com",
        )
    )
    assert isinstance(sender, SMTPEmailSender)
    assert sender._from_address == "hello@mycompany.com"
