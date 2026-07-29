from pydantic import Field

from app.schemas.base import BaseSchema


class CategoryBase(BaseSchema):
    name: str = Field(..., max_length=50)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    user_id: int


class CategoryUpdate(BaseSchema):
    name: str | None = Field(None, max_length=50)
