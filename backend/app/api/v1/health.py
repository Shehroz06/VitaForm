from fastapi import APIRouter

from app.schemas.response import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[dict])
def health_check() -> SuccessResponse[dict]:
    return SuccessResponse(message="Service is healthy.", data={"status": "ok"})
