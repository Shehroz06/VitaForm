import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.core.enums import EmploymentType


class ExperienceCreateRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=150)
    employment_type: EmploymentType
    location: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date | None = None
    is_current: bool = False

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class ExperienceUpdateRequest(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    job_title: str | None = Field(default=None, min_length=1, max_length=150)
    employment_type: EmploymentType | None = None
    location: str | None = Field(default=None, max_length=150)
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


class ExperienceResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    job_title: str
    employment_type: EmploymentType
    location: str | None
    description: str | None
    start_date: date
    end_date: date | None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
