import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.category import Category
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


def _auth_header_for(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.mark.asyncio
class TestListCategories:
    async def test_empty_list(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/categories", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_only_own_categories(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        await _create_category(session, name="My Food", user_id=test_user.id)
        await _create_category(session, name="Other Food", user_id=other_user.id)

        response = await client.get("/categories", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "My Food"
        assert body[0]["user_id"] == test_user.id

    async def test_unauthorized(self, client: AsyncClient) -> None:
        response = await client.get("/categories")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCreateCategory:
    async def test_create_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "Продукты"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Продукты"
        assert body["user_id"] == test_user.id
        assert "id" in body

    async def test_create_duplicate_name(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        await _create_category(session, name="Продукты", user_id=test_user.id)

        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "Продукты"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Category with this name already exists"

    async def test_create_same_name_allowed_for_different_users(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        await _create_category(session, name="Продукты", user_id=other_user.id)

        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "Продукты"},
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Продукты"
        assert response.json()["user_id"] == test_user.id

    async def test_create_empty_name(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": ""},
        )
        assert response.status_code == 422

    async def test_create_whitespace_name(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "   "},
        )
        assert response.status_code == 422

    async def test_create_strips_name(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/categories",
            headers=auth_headers,
            json={"name": "  Продукты  "},
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Продукты"

    async def test_create_unauthorized(self, client: AsyncClient) -> None:
        response = await client.post("/categories", json={"name": "Продукты"})
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetCategory:
    async def test_get_own_category(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Транспорт", user_id=test_user.id
        )

        response = await client.get(
            f"/categories/{category.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == category.id
        assert body["name"] == "Транспорт"

    async def test_get_foreign_category_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )

        response = await client.get(
            f"/categories/{category.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_nonexistent_category(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/categories/999999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCategory:
    async def test_update_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Старое", user_id=test_user.id
        )

        response = await client.patch(
            f"/categories/{category.id}",
            headers=auth_headers,
            json={"name": "Новое"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Новое"

    async def test_update_duplicate_name(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        await _create_category(session, name="Еда", user_id=test_user.id)
        category = await _create_category(
            session, name="Такси", user_id=test_user.id
        )

        response = await client.patch(
            f"/categories/{category.id}",
            headers=auth_headers,
            json={"name": "Еда"},
        )

        assert response.status_code == 409

    async def test_update_foreign_category_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )

        response = await client.patch(
            f"/categories/{category.id}",
            headers=auth_headers,
            json={"name": "Хак"},
        )

        assert response.status_code == 404

    async def test_update_empty_payload_returns_same_category(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Без изменений", user_id=test_user.id
        )

        response = await client.patch(
            f"/categories/{category.id}",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Без изменений"


@pytest.mark.asyncio
class TestDeleteCategory:
    async def test_delete_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        category = await _create_category(
            session, name="Удалить", user_id=test_user.id
        )

        response = await client.delete(
            f"/categories/{category.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/categories/{category.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_foreign_category_returns_404(
        self,
        client: AsyncClient,
        session: AsyncSession,
        auth_headers: dict[str, str],
    ) -> None:
        other_user = await _create_user(session, name="other_user")
        category = await _create_category(
            session, name="Чужая", user_id=other_user.id
        )

        response = await client.delete(
            f"/categories/{category.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_nonexistent_category(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.delete("/categories/999999", headers=auth_headers)
        assert response.status_code == 404
