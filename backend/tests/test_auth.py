import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User

TEST_USER_PASSWORD = "testpassword123"


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: User) -> None:
        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.name,
                "password": TEST_USER_PASSWORD,
            },
        )

        assert response.status_code == 200

        body = response.json()
        assert "access_token" in body
        assert body["access_token"]
        assert body["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.name,
                "password": "definitely-wrong-password",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect login or password"

    async def test_login_unknown_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/login",
            data={
                "username": "no_such_user",
                "password": "any-password",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect login or password"

    async def test_login_missing_username(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/auth/login",
            data={
                "password": TEST_USER_PASSWORD,
            },
        )

        assert response.status_code == 422

    async def test_login_missing_password(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.name,
            },
        )

        assert response.status_code == 422

    async def test_login_empty_credentials(self, client: AsyncClient) -> None:
        response = await client.post("/auth/login", data={})

        assert response.status_code == 422

    async def test_login_token_can_access_me(
        self, client: AsyncClient, test_user: User
    ) -> None:
        login_response = await client.post(
            "/auth/login",
            data={
                "username": test_user.name,
                "password": TEST_USER_PASSWORD,
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        me_response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_response.status_code == 200
        body = me_response.json()
        assert body["id"] == test_user.id
        assert body["name"] == test_user.name
        assert body["role"] == test_user.role


@pytest.mark.asyncio
class TestUsersMe:
    async def test_me_without_token(self, client: AsyncClient) -> None:
        response = await client.get("/users/me")

        assert response.status_code == 401

    async def test_me_with_invalid_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )

        assert response.status_code == 401

    async def test_me_with_malformed_header(self, client: AsyncClient) -> None:
        response = await client.get(
            "/users/me",
            headers={"Authorization": "NotBearer something"},
        )

        assert response.status_code == 401

    async def test_me_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200

        body = response.json()
        assert body["id"] == test_user.id
        assert body["name"] == test_user.name
        assert body["role"] == test_user.role
        assert set(body.keys()) == {"id", "name", "role"}

    async def test_me_with_token_for_missing_user(
        self,
        client: AsyncClient,
    ) -> None:
        # token for non-existent user id
        token = create_access_token(subject=999999)
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
