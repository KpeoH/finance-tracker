from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.transaction import TransactionType
from app.schemas.base import BaseSchema, ConfigDict
from app.schemas.category import CategoryRead
from app.schemas.user import UserShort


class TransactionBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0)
    type: TransactionType


class TransactionCreate(TransactionBase):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    category_id: int

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name can't be empty")
        return v


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    user: UserShort
    category: CategoryRead


class TransactionUpdate(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=100)
    amount: Decimal | None = Field(None, gt=0)
    type: TransactionType | None = None
    category_id: int | None = None
    created_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name can't be empty")
        return v
