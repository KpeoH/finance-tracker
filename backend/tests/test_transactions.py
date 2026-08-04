from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
    name: str = "Test purchase",
    amount: Decimal = Decimal("100.00"),
    type: TransactionType = TransactionType.OUTCOME,
    created_at: datetime | None = None,
) -> Transaction:
    transaction = Transaction(
        name=name,
        amount=amount,
        type=type,
        created_at=created_at or datetime.now(UTC),
        user_id=user_id,
        category_id=category_id,
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


def _auth_header_for(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _transaction_payload(
    *,
    category_id: int,
    name: str = "Кола",
    amount: str = "1.50",
    type: str = "expense",
    created_at: str | None = None,
) -> dict:
    return {
        "name": name,
        "amount": amount,
        "type": type,
        "created_at": created_at or datetime.now(UTC).isoformat(),
        "category_id": category_id,
    }


@pytest.mark.asyncio
class TestListTransactions:
    async def test_empty_list(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/transactions", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_only_own_transactions(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        my_category = await _create_category(
            session, name="Моя", user_id=test_user.id
        )
        other_user = await _create_user(session, name="other_user")
        other_category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )

        await _create_transaction(
            session,
            user_id=test_user.id,
            category_id=my_category.id,
            name="Моя транзакция",
        )
        await _create_transaction(
            session,
            user_id=other_user.id,
            category_id=other_category.id,
            name="Чужая транзакция",
        )

        response = await client.get("/transactions", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "Моя транзакция"
        assert body[0]["user"]["id"] == test_user.id

    async def test_unauthorized(self, client: AsyncClient) -> None:
        response = await client.get("/transactions")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCreateTransaction:
    async def test_create_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )

        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_transaction_payload(category_id=category.id),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Кола"
        assert Decimal(body["amount"]) == Decimal("1.50")
        assert body["type"] == "expense"
        assert body["user"]["id"] == test_user.id
        assert body["category"]["id"] == category.id
        assert "role" not in body["user"]

    async def test_create_with_foreign_category(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        foreign_category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )

        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_transaction_payload(category_id=foreign_category.id),
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid category"

    async def test_create_with_nonexistent_category(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_transaction_payload(category_id=999999),
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid category"

    async def test_create_invalid_amount(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )

        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_transaction_payload(category_id=category.id, amount="0"),
        )

        assert response.status_code == 422

    async def test_create_empty_name(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )

        response = await client.post(
            "/transactions",
            headers=auth_headers,
            json=_transaction_payload(category_id=category.id, name="   "),
        )

        assert response.status_code == 422

    async def test_create_unauthorized(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )

        response = await client.post(
            "/transactions",
            json=_transaction_payload(category_id=category.id),
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetTransaction:
    async def test_get_own_transaction(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=test_user.id,
            category_id=category.id,
            name="Молоко",
        )

        response = await client.get(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == transaction.id
        assert body["name"] == "Молоко"
        assert body["category"]["id"] == category.id

    async def test_get_foreign_transaction_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=other_user.id,
            category_id=category.id,
        )

        response = await client.get(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_nonexistent_transaction(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/transactions/999999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateTransaction:
    async def test_update_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=test_user.id,
            category_id=category.id,
            name="Старое",
            amount=Decimal("10.00"),
        )

        response = await client.patch(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
            json={"name": "Новое", "amount": "25.50"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Новое"
        assert Decimal(body["amount"]) == Decimal("25.50")

    async def test_update_category_to_foreign_one(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        my_category = await _create_category(
            session, name="Моя", user_id=test_user.id
        )
        other_user = await _create_user(session, name="other_user")
        foreign_category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=test_user.id,
            category_id=my_category.id,
        )

        response = await client.patch(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
            json={"category_id": foreign_category.id},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid category"

    async def test_update_foreign_transaction_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=other_user.id,
            category_id=category.id,
        )

        response = await client.patch(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
            json={"name": "Хак"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteTransaction:
    async def test_delete_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Продукты", user_id=test_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=test_user.id,
            category_id=category.id,
        )

        response = await client.delete(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_foreign_transaction_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )
        transaction = await _create_transaction(
            session,
            user_id=other_user.id,
            category_id=category.id,
        )

        response = await client.delete(
            f"/transactions/{transaction.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
