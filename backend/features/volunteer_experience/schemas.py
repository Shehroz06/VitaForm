import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator


class VolunteerExperienceCreateRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=150)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class VolunteerExperienceUpdateRequest(BaseModel):
    organization_name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=150)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date.")
        return self


class VolunteerExperienceResponse(BaseModel):
    id: uuid.UUID
    organization_name: str
    role: str
    start_date: date
    end_date: date | None
    is_current: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
