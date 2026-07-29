from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.transaction import TransactionType
from app.schemas.base import BaseSchema
from app.schemas.category import CategoryRead
from app.schemas.user import UserRead


class TransactionBase(BaseSchema):
    name: str = Field(..., max_length=100)
    amount: Decimal = Field(..., gt=0)
    type: TransactionType


class TransactionCreate(TransactionBase):
    created_at: datetime
    category_id: int


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    user: UserRead
    category: CategoryRead


class TransactionUpdate(BaseSchema):
    name: str | None = Field(None, max_length=100)
    amount: Decimal | None = Field(None, gt=0)
    type: TransactionType | None = None
    category_id: int | None = None
    created_at: datetime | None = None
