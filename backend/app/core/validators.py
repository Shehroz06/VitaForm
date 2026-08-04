import re

_URL_PATTERN = re.compile(r"^https?://[^\s]+\.[^\s]+$")


def validate_optional_url(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not _URL_PATTERN.match(value):
        raise ValueError("Must be a valid URL starting with http:// or https://")
    return value
