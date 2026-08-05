import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.enums import FilePurpose


class FileResponse(BaseModel):
    id: uuid.UUID
    purpose: FilePurpose
    original_filename: str
    content_type: str
    size_bytes: int
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
