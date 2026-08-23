"""Small HTTP-response helpers shared across features that echo
user-controlled strings back into response headers."""

import re
from urllib.parse import quote

_UNSAFE_HEADER_CHARS = re.compile(r'[\r\n"\\]')


def content_disposition(filename: str, disposition: str = "attachment") -> str:
    """Builds a Content-Disposition header value that stays safe even when
    `filename` is user-controlled: CR/LF/quote/backslash are stripped from
    the plain `filename=` fallback (blocking header injection and
    quote-breakout), and the full name is preserved via the RFC 6266
    `filename*` extended parameter."""
    ascii_only = filename.encode("ascii", "replace").decode("ascii")
    ascii_fallback = _UNSAFE_HEADER_CHARS.sub("_", ascii_only) or "file"
    return f'{disposition}; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quote(filename)}'
