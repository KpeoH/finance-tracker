from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, ConfigDict


class CategoryBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name can't be empty")
        return v


class CategoryRead(CategoryBase):
    id: int
    user_id: int


class CategoryUpdate(BaseSchema):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(None, min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name can't be empty")
        return v
