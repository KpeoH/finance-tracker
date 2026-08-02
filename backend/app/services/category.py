from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryService:
    @staticmethod
    async def get_by_id(session: AsyncSession, category_id: int) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(
        session: AsyncSession, name: str, user_id: int
    ) -> Category | None:
        stmt = select(Category).where(
            Category.name == name, Category.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(session: AsyncSession, user_id: int) -> list[Category]:
        stmt = select(Category).where(Category.user_id == user_id).order_by(Category.id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def count_by_user(session: AsyncSession, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Category)
            .where(Category.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def create(session: AsyncSession, name: str, user_id: int) -> Category:
        category = Category(name=name, user_id=user_id)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def update(session: AsyncSession, category: Category, name: str) -> Category:
        category.name = name
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(session: AsyncSession, category: Category) -> None:
        await session.delete(category)
        await session.commit()
