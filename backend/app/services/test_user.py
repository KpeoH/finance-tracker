from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


def _month_start(dt: datetime, months_ago: int = 0) -> datetime:
    """Return UTC datetime at the beginning of the target month."""
    year = dt.year
    month = dt.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1, tzinfo=UTC)


def build_seed_transactions(
    products_id: int,
    salary_id: int,
    now: datetime | None = None,
) -> list[dict]:
    """Build 6 demo transactions: 3 for previous month, 3 for current."""
    if now is None:
        now = datetime.now(UTC)

    prev_month = _month_start(now, months_ago=1)
    curr_month = _month_start(now, months_ago=0)

    return [
        # previous month
        {
            "name": "Пятёрочка",
            "amount": Decimal("1250.00"),
            "type": TransactionType.OUTCOME,
            "created_at": prev_month + timedelta(days=3, hours=14),
            "category_id": products_id,
        },
        {
            "name": "Зарплата",
            "amount": Decimal("75000.00"),
            "type": TransactionType.INCOME,
            "created_at": prev_month + timedelta(days=5, hours=10),
            "category_id": salary_id,
        },
        {
            "name": "Лента",
            "amount": Decimal("3200.50"),
            "type": TransactionType.OUTCOME,
            "created_at": prev_month + timedelta(days=18, hours=19),
            "category_id": products_id,
        },
        # current month
        {
            "name": "Магнит",
            "amount": Decimal("890.00"),
            "type": TransactionType.OUTCOME,
            "created_at": curr_month + timedelta(days=1, hours=12),
            "category_id": products_id,
        },
        {
            "name": "Аванс",
            "amount": Decimal("30000.00"),
            "type": TransactionType.INCOME,
            "created_at": curr_month + timedelta(days=2, hours=9),
            "category_id": salary_id,
        },
        {
            "name": "ВкусВилл",
            "amount": Decimal("1450.00"),
            "type": TransactionType.OUTCOME,
            "created_at": curr_month + timedelta(days=4, hours=16),
            "category_id": products_id,
        },
    ]


class TestUserService:
    @staticmethod
    async def get_test_user(session: AsyncSession) -> User | None:
        stmt = select(User).where(User.role == "test")
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def clear_data(session: AsyncSession, user_id: int) -> None:
        await session.execute(delete(Transaction).where(Transaction.user_id == user_id))
        await session.execute(delete(Category).where(Category.user_id == user_id))
        await session.commit()

    @staticmethod
    async def seed_data(session: AsyncSession, user_id: int) -> None:
        products = Category(name="Продукты", user_id=user_id)
        salary = Category(name="Зарплата", user_id=user_id)
        session.add_all([products, salary])
        await session.flush()

        seed_rows = build_seed_transactions(products.id, salary.id)
        transactions = [
            Transaction(
                name=row["name"],
                amount=row["amount"],
                type=row["type"],
                created_at=row["created_at"],
                user_id=user_id,
                category_id=row["category_id"],
            )
            for row in seed_rows
        ]
        session.add_all(transactions)
        await session.commit()

    @staticmethod
    async def reset(session: AsyncSession) -> User:
        user = await TestUserService.get_test_user(session)
        if user is None:
            raise RuntimeError("Test user (role='test') not found")

        await TestUserService.clear_data(session, user.id)
        await TestUserService.seed_data(session, user.id)
        return user
