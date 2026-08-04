import math
from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int
    limit: int


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


def build_pagination_meta(page: int, limit: int, total: int) -> dict[str, Any]:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if limit else 0,
    }
