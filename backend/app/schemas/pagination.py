import math
from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int
    limit: int
    sort: str | None = None


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: Annotated[
        str | None,
        Query(description="Field to sort by; prefix with '-' for descending, e.g. -created_at"),
    ] = None,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit, sort=sort)


def build_pagination_meta(page: int, limit: int, total: int) -> dict[str, Any]:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if limit else 0,
    }
