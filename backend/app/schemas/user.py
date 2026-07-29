from pydantic import Field

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    name: str = Field(..., max_length=50)
    role: str = Field(..., max_length=5)


class UserRead(UserBase):
    id: int
