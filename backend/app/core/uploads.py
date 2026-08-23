from fastapi import UploadFile

from app.exceptions.base import ValidationException

_CHUNK_SIZE = 1024 * 1024


async def read_upload_capped(upload_file: UploadFile, max_bytes: int, error_message: str) -> bytes:
    """Reads an upload in chunks, aborting as soon as `max_bytes` is
    exceeded instead of buffering an unbounded body into memory first."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload_file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValidationException(error_message)
        chunks.append(chunk)
    return b"".join(chunks)
