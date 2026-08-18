import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import ImportSessionStatus


class ImportSessionResponse(BaseModel):
    id: uuid.UUID
    source_filename: str
    status: ImportSessionStatus
    proposed_data: dict[str, Any]
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportConfirmRequest(BaseModel):
    """The user's final, possibly-edited/filtered selection -- the same
    shape as ImportSessionResponse.proposed_data, but never trusted as
    equal to it. Every item is re-validated against the real per-resource
    CreateRequest schema before anything is written."""

    bio: str | None = None
    sections: dict[str, list[dict[str, Any]]] = {}


class ImportConfirmResultResponse(BaseModel):
    created_counts: dict[str, int]
    profile_headline_updated: bool
