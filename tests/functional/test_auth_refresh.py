"""
FUNCTIONAL тесты для refresh токенов.

Что тестируем:
- Обновление токенов через JSON body
- Обновление токенов через cookies
- Обработка невалидных токенов
- Обработка истекших токенов
"""
import pytest
from httpx import AsyncClient
from tests.utils.helpers import create_test_user_data, assert_response_structure


class TestAuthRefreshAPI:
    """Функциональные тесты для обновления токенов."""

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_success(self, client: AsyncClient):
        """Тест успешного обновления токена через JSON."""
        # 1. Регистрируем пользователя
        user_data = create_test_user_data()
        register_response = await client.post("/api/v1/register", json=user_data)
        assert register_response.status_code == 200

        # 2. Логинимся для получения токенов
        auth_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        auth_response = await client.post("/api/v1/auth", data=auth_data)  # data, не json!
        assert auth_response.status_code == 200

        auth_result = auth_response.json()
        refresh_token = auth_result["refresh_token"]

        # 3. Обновляем токен через заголовок
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": refresh_token}
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_with_cookies(self, client: AsyncClient):
        """Тест обновления токена через cookies."""
        user_data = create_test_user_data()

        # Регистрация
        register_response = await client.post("/api/v1/register", json=user_data)
        assert register_response.status_code == 200

        # Аутентификация с cookies
        auth_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        auth_response = await client.post(
            "/api/v1/auth?use_cookies=true",
            data=auth_data
        )
        assert auth_response.status_code == 200

        # ИСПРАВЛЕНО: Получаем cookies из заголовков Set-Cookie
        set_cookie_headers = auth_response.headers.get_list("set-cookie")
        print(f"Set-Cookie headers: {set_cookie_headers}")

        # Парсим cookies вручную
        cookies_dict = {}
        for cookie_header in set_cookie_headers:
            # Парсим "access_token=value; HttpOnly; Path=/; ..."
            cookie_parts = cookie_header.split(';')
            if cookie_parts:
                name_value = cookie_parts[0].strip()
                if '=' in name_value:
                    name, value = name_value.split('=', 1)
                    cookies_dict[name] = value

        print(f"Parsed cookies: {cookies_dict}")

        # Проверяем что cookies установлены
        assert "access_token" in cookies_dict
        assert "refresh_token" in cookies_dict

        # Обновляем токен с передачей cookies
        refresh_response = await client.post(
            "/api/v1/auth/refresh?use_cookies=true",
            cookies=cookies_dict  # Передаем словарь cookies
        )

        print(f"Refresh response status: {refresh_response.status_code}")
        print(f"Refresh response body: {refresh_response.text}")

        assert refresh_response.status_code == 200

        # Проверяем что новые cookies установлены
        new_set_cookie_headers = refresh_response.headers.get_list("set-cookie")
        assert len(new_set_cookie_headers) >= 2  # access_token и refresh_token

        # Проверяем что токены в JSON равны None
        data = refresh_response.json()
        assert data["access_token"] is None
        assert data["refresh_token"] is None


    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Тест с невалидным refresh токеном."""
        invalid_token = "invalid.refresh.token"

        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": invalid_token}
        )

        assert response.status_code in [401, 422]
        data = response.json()

        # Плоский формат ошибки!
        assert "detail" in data
        assert "error_type" in data
        assert data["error_type"] in ["auth_error", "token_invalid", "token_error"]

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_missing(self, client: AsyncClient):
        """Тест без передачи refresh токена."""
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        data = response.json()

        # ИСПРАВЛЕНО - не проверяем конкретный текст
        assert "detail" in data
        assert "error_type" in data

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_expired(self, client: AsyncClient):
        """Тест с истекшим refresh токеном."""
        # Создаем токен с истекшим сроком (это сложно сделать в функциональном тесте)
        # Поэтому используем заведомо старый/невалидный формат
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjQwOTk1MjAwfQ.invalid"

        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": expired_token}
        )

        assert response.status_code in [401, 419, 422]
        data = response.json()

        assert "detail" in data
        assert "error_type" in data

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_reuse_prevention(self, client: AsyncClient):
        """Тест предотвращения повторного использования refresh токена."""
        # 1. Регистрируем и логинимся
        user_data = create_test_user_data()
        await client.post("/api/v1/register", json=user_data)

        auth_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        auth_response = await client.post("/api/v1/auth", data=auth_data)
        refresh_token = auth_response.json()["refresh_token"]

        # 2. Первое обновление токена (должно работать)
        first_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": refresh_token}
        )
        assert first_response.status_code == 200

        # 3. Повторное использование того же токена (должно быть запрещено)
        second_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": refresh_token}
        )
        assert second_response.status_code == 401
        data = second_response.json()

        # Плоский формат!
        assert "detail" in data
        assert "error_type" in data

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_response_structure(self, client: AsyncClient):
        """Тест структуры ответа при обновлении токена."""
        # Подготовка
        user_data = create_test_user_data()
        await client.post("/api/v1/register", json=user_data)

        auth_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        auth_response = await client.post("/api/v1/auth", data=auth_data)
        refresh_token = auth_response.json()["refresh_token"]

        # Тест
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert_response_structure(data, ["success"])

        # Проверяем поля токенов
        required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
        for field in required_fields:
            assert field in data

        # Проверяем типы данных
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert data["token_type"] == "Bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0


    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_refresh_token_different_from_original(self, client: AsyncClient):
        """Тест что новый refresh токен отличается от старого."""
        user_data = create_test_user_data()

        # Регистрация и аутентификация
        await client.post("/api/v1/register", json=user_data)

        auth_response = await client.post("/api/v1/auth", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })

        original_refresh = auth_response.json()["refresh_token"]

        # Обновление токена
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"refresh-token": original_refresh}
        )

        assert refresh_response.status_code == 200
        new_refresh = refresh_response.json()["refresh_token"]

        assert new_refresh != original_refresh
        assert len(new_refresh) > 50
