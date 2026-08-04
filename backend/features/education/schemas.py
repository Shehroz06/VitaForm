import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator


class EducationCreateRequest(BaseModel):
    institution_name: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=150)
    grade: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date | None = None
    is_current: bool = False

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class EducationUpdateRequest(BaseModel):
    institution_name: str | None = Field(default=None, min_length=1, max_length=200)
    degree: str | None = Field(default=None, min_length=1, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=150)
    grade: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date.")
        return self


class EducationResponse(BaseModel):
    id: uuid.UUID
    institution_name: str
    degree: str
    field_of_study: str | None
    grade: str | None
    description: str | None
    start_date: date
    end_date: date | None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
