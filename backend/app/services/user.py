from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User


class UserService:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> User | None:
        stmt = select(User).where(User.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate(
        session: AsyncSession,
        name: str,
        password: str,
    ) -> User | None:
        user = await UserService.get_by_name(session, name)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user
