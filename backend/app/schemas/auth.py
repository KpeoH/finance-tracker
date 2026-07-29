from pydantic import Field

from app.schemas.base import BaseSchema


class UserLogin(BaseSchema):
    name: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
