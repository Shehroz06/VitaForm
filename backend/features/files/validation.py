from dataclasses import dataclass

from app.config.settings import Settings
from app.core.enums import FilePurpose
from app.exceptions.base import ValidationException

_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp", "gif"})
_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})

_DOCUMENT_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "pdf"})
_DOCUMENT_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "application/pdf"})


@dataclass(frozen=True)
class _UploadRules:
    allowed_extensions: frozenset[str]
    allowed_content_types: frozenset[str]
    max_size_bytes: int


def _rules_for(purpose: FilePurpose, settings: Settings) -> _UploadRules:
    if purpose is FilePurpose.AVATAR:
        return _UploadRules(
            _IMAGE_EXTENSIONS, _IMAGE_CONTENT_TYPES, settings.max_avatar_size_mb * 1024 * 1024
        )
    return _UploadRules(
        _DOCUMENT_EXTENSIONS,
        _DOCUMENT_CONTENT_TYPES,
        settings.max_attachment_size_mb * 1024 * 1024,
    )


def validate_upload(
    purpose: FilePurpose,
    filename: str | None,
    content_type: str | None,
    size_bytes: int,
    settings: Settings,
) -> str:
    """Validates an upload against purpose-specific rules and returns the
    lowercased file extension (without the dot) on success."""
    rules = _rules_for(purpose, settings)

    if size_bytes == 0:
        raise ValidationException("Uploaded file is empty.")
    if size_bytes > rules.max_size_bytes:
        max_mb = rules.max_size_bytes // (1024 * 1024)
        raise ValidationException(f"File exceeds the maximum size of {max_mb}MB.")

    if not filename or "." not in filename:
        raise ValidationException("File must have a valid extension.")
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in rules.allowed_extensions:
        allowed = ", ".join(sorted(rules.allowed_extensions))
        raise ValidationException(f"File extension must be one of: {allowed}.")

    if content_type not in rules.allowed_content_types:
        allowed_types = ", ".join(sorted(rules.allowed_content_types))
        raise ValidationException(f"File type must be one of: {allowed_types}.")

    return extension
