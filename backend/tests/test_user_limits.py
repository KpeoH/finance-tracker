from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


async def _create_user(
    session: AsyncSession,
    *,
    name: str,
    role: str = "user",
) -> User:
    user = User(
        name=name,
        password_hash=hash_password("password123"),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_category(
    session: AsyncSession,
    *,
    name: str,
    user_id: int,
) -> Category:
    category = Category(name=name, user_id=user_id)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def _create_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: int,
    name: str = "Seed tx",
) -> Transaction:
    transaction = Transaction(
        name=name,
        amount=Decimal("10.00"),
        type=TransactionType.OUTCOME,
        created_at=datetime.now(UTC),
        user_id=user_id,
        category_id=category_id,
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _tx_payload(category_id: int, name: str = "Test TX") -> dict:
    return {
        "name": name,
        "amount": "12.50",
        "type": "expense",
        "created_at": datetime.now(UTC).isoformat(),
        "category_id": category_id,
    }


@pytest.mark.asyncio
class TestCategoryLimitsForTestUser:
    async def test_allows_creation_within_limit(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        test_user = await _create_user(session, name="limit_cat_user", role="test")
        headers = _auth_headers(test_user.id)

        for i in range(settings.TEST_USER_MAX_CATEGORIES):
            response = await client.post(
                "/categories",
                headers=headers,
                json={"name": f"Cat {i}"},
            )
            assert response.status_code == 201, response.text

    async def test_blocks_category_over_limit(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        test_user = await _create_user(session, name="limit_cat_block", role="test")
        headers = _auth_headers(test_user.id)

        for i in range(settings.TEST_USER_MAX_CATEGORIES):
            await _create_category(
                session,
                name=f"Existing {i}",
                user_id=test_user.id,
            )

        response = await client.post(
            "/categories",
            headers=headers,
            json={"name": "Over limit"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Test user category limit reached"

    async def test_regular_user_is_not_limited(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        # even if regular user already has many categories, limit must not apply
        for i in range(settings.TEST_USER_MAX_CATEGORIES + 3):
            await _create_category(
                session,
                name=f"Regular {i}",
                user_id=test_user.id,
            )

        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "Still allowed"},
        )

        assert response.status_code == 201


@pytest.mark.asyncio
class TestTransactionLimitsForTestUser:
    async def test_allows_creation_within_limit(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        test_user = await _create_user(session, name="limit_tx_user", role="test")
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )
        headers = _auth_headers(test_user.id)

        for i in range(settings.TEST_USER_MAX_TRANSACTIONS):
            response = await client.post(
                "/transactions",
                headers=headers,
                json=_tx_payload(category.id, name=f"TX {i}"),
            )
            assert response.status_code == 201, response.text

    async def test_blocks_transaction_over_limit(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        test_user = await _create_user(session, name="limit_tx_block", role="test")
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )
        headers = _auth_headers(test_user.id)

        for i in range(settings.TEST_USER_MAX_TRANSACTIONS):
            await _create_transaction(
                session,
                user_id=test_user.id,
                category_id=category.id,
                name=f"Existing TX {i}",
            )

        response = await client.post(
            "/transactions",
            headers=headers,
            json=_tx_payload(category.id, name="Over limit"),
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Test user transaction limit reached"

    async def test_regular_user_is_not_limited(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )

        for i in range(settings.TEST_USER_MAX_TRANSACTIONS + 3):
            await _create_transaction(
                session,
                user_id=test_user.id,
                category_id=category.id,
                name=f"Regular TX {i}",
            )

        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_tx_payload(category.id, name="Still allowed"),
        )

        assert response.status_code == 201
