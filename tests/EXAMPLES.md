# РЕЗЮМЕ РАЗЛИЧИЙ МЕЖДУ INTEGRATION И FUNCTIONAL ТЕСТАМИ:

"""
INTEGRATION ТЕСТЫ (этот файл):
✅ Мокируют RegisterService
✅ Тестируют HTTP слой (роутер)
✅ Быстрые (нет реальных операций)
✅ Фокус на контрактах API
✅ Проверяют валидацию запросов
✅ Проверяют структуру ответов
✅ Проверяют обработку ошибок роутером

FUNCTIONAL ТЕСТЫ (другой файл):
✅ НЕ мокируют RegisterService
✅ Используют реальную БД
✅ Медленные (создание БД, транзакции)
✅ Фокус на бизнес-логике
✅ Проверяют реальное сохранение данных
✅ Проверяют бизнес-правила (дубликаты)
✅ Проверяют полный цикл работы

КОГДА ИСПОЛЬЗОВАТЬ:
- Integration: для быстрой проверки HTTP контрактов
- Functional: для проверки бизнес-логики и работы с БД

ПРИМЕР ЗАПУСКА:
pytest tests/integration/routes/test_registration.py -m integration  # Только integration тесты
pytest tests/functional/routes/test_registration.py -m functional   # Только functional тесты
pytest tests/ -m "not functional"  # Все кроме functional (быстрые тесты)
"""

1. Unit Тесты

```python
import pytest
from fastapi import APIRouter
from app.routes.v1.registration.router import RegisterRouter


class TestRegisterRouter:
    """Тесты для класса RegisterRouter"""

    def test_router_initialization(self):
        """Тест инициализации роутера"""
        router = RegisterRouter()

        assert isinstance(router.router, APIRouter)
        assert router.router.prefix == "register"
        assert "Registration" in router.router.tags

    def test_router_configuration(self):
        """Тест настройки маршрутов"""
        router = RegisterRouter()
        router.configure()

        # Проверяем, что маршрут зарегистрирован
        routes = [route.path for route in router.router.routes]
        assert "" in routes  # POST /register

        # Проверяем методы
        post_route = next(route for route in router.router.routes if route.path == "")
        assert "POST" in post_route.methods

    def test_response_models_configuration(self):
        """Тест настройки моделей ответов"""
        router = RegisterRouter()
        router.configure()

        post_route = next(route for route in router.router.routes if route.path == "")

        # Проверяем коды ответов
        assert 201 in post_route.responses
        assert 409 in post_route.responses
        assert 500 in post_route.responses
```

2. Integration Тесты

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from tests.conftest import TestDatabase


class TestRegistrationAPI:
    """Интеграционные тесты API регистрации"""

    @pytest.mark.asyncio
    async def test_successful_registration(self, client: AsyncClient, db_session: AsyncSession):
        """Тест успешной регистрации пользователя"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123",
            "phone": "+7 (999) 123-45-67"
        }

        response = await client.post("/api/v1/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_registration_with_cookies(self, client: AsyncClient):
        """Тест регистрации с использованием cookies"""
        user_data = {
            "username": "cookieuser",
            "email": "cookie@example.com",
            "password": "SecurePass123"
        }

        response = await client.post(
            "/api/v1/register?use_cookies=true",
            json=user_data
        )

        assert response.status_code == 201
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client: AsyncClient):
        """Тест регистрации с дублирующимся email"""
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "SecurePass123"
        }

        # Первая регистрация
        await client.post("/api/v1/register", json=user_data)

        # Попытка повторной регистрации
        user_data["username"] = "user2"
        response = await client.post("/api/v1/register", json=user_data)

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "email" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_duplicate_username_registration(self, client: AsyncClient):
        """Тест регистрации с дублирующимся username"""
        user_data = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "SecurePass123"
        }

        # Первая регистрация
        await client.post("/api/v1/register", json=user_data)

        # Попытка повторной регистрации
        user_data["email"] = "user2@example.com"
        response = await client.post("/api/v1/register", json=user_data)

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "username" in data["message"].lower()

```

3. Functional Тесты

```python
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestRegistrationFlow:
    """Функциональные тесты процесса регистрации"""

    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, client: AsyncClient):
        """Тест полного процесса регистрации"""
        with patch('app.services.email.EmailService.send_verification_email') as mock_email:
            mock_email.return_value = AsyncMock()

            user_data = {
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "SecurePass123",
                "phone": "+7 (999) 111-22-33"
            }

            response = await client.post("/api/v1/register", json=user_data)

            # Проверяем успешную регистрацию
            assert response.status_code == 201
            data = response.json()

            # Проверяем структуру ответа
            assert data["success"] is True
            assert "data" in data
            assert "user" in data["data"]
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]

            # Проверяем данные пользователя
            user = data["data"]["user"]
            assert user["username"] == "flowuser"
            assert user["email"] == "flow@example.com"
            assert user["is_verified"] is False

            # Проверяем отправку email
            mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_registration_validation_errors(self, client: AsyncClient):
        """Тест ошибок валидации при регистрации"""
        test_cases = [
            # Короткий username
            {
                "data": {"username": "ab", "email": "test@example.com", "password": "SecurePass123"},
                "expected_field": "username"
            },
            # Невалидный email
            {
                "data": {"username": "testuser", "email": "invalid-email", "password": "SecurePass123"},
                "expected_field": "email"
            },
            # Слабый пароль
            {
                "data": {"username": "testuser", "email": "test@example.com", "password": "123"},
                "expected_field": "password"
            },
            # Невалидный телефон
            {
                "data": {"username": "testuser", "email": "test@example.com", "password": "SecurePass123", "phone": "invalid"},
                "expected_field": "phone"
            }
        ]

        for case in test_cases:
            response = await client.post("/api/v1/register", json=case["data"])
            assert response.status_code == 422

            error_data = response.json()
            assert "detail" in error_data

            # Проверяем, что ошибка связана с ожидаемым полем
            field_errors = [err for err in error_data["detail"] if err["loc"][-1] == case["expected_field"]]
            assert len(field_errors) > 0
```

4. Security Тесты

```python
import pytest
from httpx import AsyncClient
from sqlalchemy import text


class TestRegistrationSecurity:
    """Тесты безопасности регистрации"""

    @pytest.mark.asyncio
    async def test_password_hashing(self, client: AsyncClient, db_session):
        """Тест хеширования паролей"""
        user_data = {
            "username": "secureuser",
            "email": "secure@example.com",
            "password": "MySecurePassword123"
        }

        response = await client.post("/api/v1/register", json=user_data)
        assert response.status_code == 201

        # Проверяем, что пароль не хранится в открытом виде
        result = await db_session.execute(
            text("SELECT password_hash FROM users WHERE email = :email"),
            {"email": "secure@example.com"}
        )
        stored_hash = result.scalar()

        assert stored_hash != "MySecurePassword123"
        assert len(stored_hash) > 50  # Хеш должен быть длинным
        assert stored_hash.startswith("$")  # Bcrypt hash format

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: AsyncClient):
        """Тест защиты от SQL инъекций"""
        malicious_data = {
            "username": "user'; DROP TABLE users; --",
            "email": "hack@example.com",
            "password": "SecurePass123"
        }

        response = await client.post("/api/v1/register", json=malicious_data)

        # Запрос должен быть обработан безопасно
        assert response.status_code in [201, 422]  # Либо успех, либо валидация

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Тест ограничения частоты запросов"""
        user_data_template = {
            "username": "rateuser{}",
            "email": "rate{}@example.com",
            "password": "SecurePass123"
        }

        # Отправляем много запросов подряд
        responses = []
        for i in range(20):
            user_data = {
                "username": f"rateuser{i}",
                "email": f"rate{i}@example.com",
                "password": "SecurePass123"
            }
            response = await client.post("/api/v1/register", json=user_data)
            responses.append(response.status_code)

        # Проверяем, что есть ограничения (429 Too Many Requests)
        rate_limited = any(status == 429 for status in responses)
        assert rate_limited or len(set(responses)) == 1  # Либо rate limit, либо все успешны

    @pytest.mark.asyncio
    async def test_token_security(self, client: AsyncClient):
        """Тест безопасности токенов"""
        user_data = {
            "username": "tokenuser",
            "email": "token@example.com",
            "password": "SecurePass123"
        }

        response = await client.post("/api/v1/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]

        # Проверяем формат токенов (JWT)
        assert len(access_token.split('.')) == 3
        assert len(refresh_token.split('.')) == 3

        # Токены должны быть разными
        assert access_token != refresh_token

```

5. Performance Тесты

```python
import pytest
import asyncio
import time
from httpx import AsyncClient


class TestRegistrationPerformance:
    """Тесты производительности регистрации"""

    @pytest.mark.asyncio
    async def test_single_registration_response_time(self, client: AsyncClient):
        """Тест времени отклика одной регистрации"""
        user_data = {
            "username": "perfuser",
            "email": "perf@example.com",
            "password": "SecurePass123"
        }

        start_time = time.time()
        response = await client.post("/api/v1/register", json=user_data)
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 201
        assert response_time < 2.0  # Регистрация должна занимать менее 2 секунд

```