from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction, TransactionType


class TransactionService:
    @staticmethod
    async def get_by_id(
        session: AsyncSession, transaction_id: int
    ) -> Transaction | None:
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.user), selectinload(Transaction.category))
            .where(Transaction.id == transaction_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(session: AsyncSession, user_id: int) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.user), selectinload(Transaction.category))
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def count_by_user(session: AsyncSession, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        amount: Decimal,
        type: TransactionType,
        created_at: datetime,
        user_id: int,
        category_id: int,
    ) -> Transaction:
        transaction = Transaction(
            name=name,
            amount=amount,
            type=type,
            created_at=created_at,
            user_id=user_id,
            category_id=category_id,
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return await TransactionService.get_by_id(session, transaction.id)

    @staticmethod
    async def update(
        session: AsyncSession,
        transaction: Transaction,
        *,
        name: str | None = None,
        amount: Decimal | None = None,
        type: TransactionType | None = None,
        category_id: int | None = None,
        created_at: datetime | None = None,
    ) -> Transaction:
        if name is not None:
            transaction.name = name
        if amount is not None:
            transaction.amount = amount
        if type is not None:
            transaction.type = type
        if category_id is not None:
            transaction.category_id = category_id
        if created_at is not None:
            transaction.created_at = created_at

        await session.commit()
        await session.refresh(transaction)
        return await TransactionService.get_by_id(session, transaction.id)

    @staticmethod
    async def delete(session: AsyncSession, transaction: Transaction) -> None:
        await session.delete(transaction)
        await session.commit()
