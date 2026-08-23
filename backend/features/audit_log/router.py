from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.audit_log.dependencies import get_audit_log_repository
from features.audit_log.models import AuditLog
from features.audit_log.repository import AuditLogRepository
from features.audit_log.schemas import AuditLogResponse
from features.profiles.dependencies import CurrentProfile

router = APIRouter(tags=["audit-log"])

AuditLogRepositoryDep = Annotated[AuditLogRepository, Depends(get_audit_log_repository)]


@router.get("/audit-log", response_model=SuccessResponse[list[AuditLogResponse]])
async def list_audit_log(
    profile: CurrentProfile,
    repository: AuditLogRepositoryDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[AuditLogResponse]]:
    """Your own action history -- every create/update/delete recorded
    automatically across your profile's resources (see app/core/audit.py).
    Read-only: nothing can write here except that listener."""
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "created_at": AuditLog.created_at,
            "action": AuditLog.action,
            "resource_type": AuditLog.resource_type,
        },
        default=AuditLog.created_at,
        default_desc=True,
    )
    items, total = await repository.list_for_profile(
        profile.id, page=pagination.page, limit=pagination.limit, sort_columns=sort_columns
    )
    return SuccessResponse(
        message="Audit log retrieved successfully.",
        data=[AuditLogResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )
