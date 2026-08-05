"""Storage abstraction so the app never talks to a disk or a bucket directly.

Local dev writes to disk; production points STORAGE_PROVIDER at "s3" (any
S3-compatible endpoint — AWS S3, Cloudflare R2, MinIO). Swapping providers is
a config change, not a code change, per the provider-independence rule that
already governs the AI layer.
"""

import asyncio
from pathlib import Path
from typing import Protocol


class StorageProvider(Protocol):
    async def save(self, key: str, content: bytes, content_type: str) -> None: ...

    async def read(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...

    def get_signed_url(self, key: str) -> str | None:
        """A time-limited direct URL to the object, if the backend supports one
        (S3). Returns None for backends (local disk) that have no signing
        concept — callers fall back to streaming bytes through the app."""
        ...


class LocalStorageProvider:
    """Dev-only backend: files live under a directory on the container's disk."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path.resolve()
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, key: str, content: bytes, content_type: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, content)

    async def read(self, key: str) -> bytes:
        return await asyncio.to_thread(self._resolve(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._resolve(key).unlink, True)

    def get_signed_url(self, key: str) -> str | None:
        return None

    def _resolve(self, key: str) -> Path:
        resolved = (self._base_path / key).resolve()
        if not resolved.is_relative_to(self._base_path):
            raise ValueError("Invalid storage key.")
        return resolved


class S3StorageProvider:
    """S3-compatible backend for production. Structurally complete but not
    exercised in this environment — no bucket/credentials are configured here.
    Wire up by setting STORAGE_PROVIDER=s3 plus the S3_* settings."""

    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> None:
        import boto3

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    async def save(self, key: str, content: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    async def read(self, key: str) -> bytes:
        response = await asyncio.to_thread(self._client.get_object, Bucket=self._bucket, Key=key)
        body: bytes = response["Body"].read()
        return body

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)

    def get_signed_url(self, key: str) -> str | None:
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=3600,
        )
        return url
