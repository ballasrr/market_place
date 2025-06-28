"""Тесты для роутера пользователей."""
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from tests.utils.helpers import assert_response_structure, create_mock_user_data


class TestUserRouter:
    """Тесты для UserRouter."""

    @pytest.mark.asyncio
    async def test_get_users_success(self, auth_client: AsyncClient):
        """Тест успешного получения списка пользователей."""
        with patch('app.services.v1.users.service.UserService.get_users') as mock_get_users:
            mock_users = [
                create_mock_user_data(1),
                create_mock_user_data(2)
            ]
            mock_get_users.return_value = (mock_users, 2)

            response = await auth_client.get("/api/v1/users")

            assert response.status_code == 200
            response_data = response.json()

            assert_response_structure(response_data, ["data"])
            assert "items" in response_data["data"]
            assert "total" in response_data["data"]
            assert "page" in response_data["data"]
            assert "size" in response_data["data"]
            assert len(response_data["data"]["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(self, auth_client: AsyncClient):
        """Тест получения пользователей с пагинацией."""
        with patch('app.services.v1.users.service.UserService.get_users') as mock_get_users:
            mock_get_users.return_value = ([], 0)

            response = await auth_client.get("/api/v1/users?skip=10&limit=5")

            assert response.status_code == 200
            mock_get_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users_unauthorized(self, client: AsyncClient):
        """Тест получения пользователей без авторизации."""
        response = await client.get("/api/v1/users")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_users_large_dataset(self, auth_client: AsyncClient):
        """Тест с большим количеством пользователей."""
        with patch('app.services.v1.users.service.UserService.get_users') as mock_get_users:
            mock_users = [create_mock_user_data(i) for i in range(1, 101)]
            mock_get_users.return_value = (mock_users, 1000)

            response = await auth_client.get("/api/v1/users?limit=100")

            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data["data"]["items"]) == 100
            assert response_data["data"]["total"] == 1000

    @pytest.mark.asyncio
    async def test_get_users_response_schema_validation(self, auth_client: AsyncClient):
        """Тест валидации схемы ответа."""
        with patch('app.services.v1.users.service.UserService.get_users') as mock_get_users:
            mock_users = [create_mock_user_data(1)]
            mock_get_users.return_value = (mock_users, 1)

            response = await auth_client.get("/api/v1/users")

            assert response.status_code == 200
            response_data = response.json()

            # Проверяем структуру ответа
            assert "data" in response_data
            data = response_data["data"]
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data

            # Проверяем структуру элементов
            assert len(data["items"]) == 1
            user = data["items"][0]
            required_fields = ["id", "username", "email", "role", "is_verified"]
            for field in required_fields:
                assert field in user
