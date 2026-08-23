import uuid
from datetime import datetime

from pydantic import BaseModel

from features.audit_log.models import AuditAction


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: AuditAction
    resource_type: str
    resource_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
