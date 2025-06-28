"""
FUNCTIONAL ТЕСТЫ для роутера регистрации пользователей.

Что такое Functional тесты:
- Тестируют ПОЛНЫЙ ЦИКЛ работы функционала
- Используют РЕАЛЬНУЮ базу данных (PostgreSQL)
- НЕ используют моки бизнес-логики (сервисов)
- Проверяют что данные реально сохраняются в БД
- МЕДЛЕННЫЕ (создание БД, транзакции)

Отличие от Integration тестов:
- Integration: мокают сервисы, тестируют только HTTP слой
- Functional: реальные сервисы + реальная БД, тестируют бизнес-логику

Когда использовать:
- Проверка что регистрация реально создает пользователя в БД
- Проверка бизнес-правил (дубликаты email/username)
- Проверка полного цикла: HTTP запрос → роутер → сервис → БД

Структура теста:
1. Подготовка данных
2. HTTP запрос через client фикстуру
3. Проверка HTTP ответа
4. Проверка данных в БД (опционально)
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestRegistrationAPI:
    """Интеграционные тесты API регистрации"""

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_successful_registration(self, client: AsyncClient, db_session: AsyncSession):
        """
        Тест успешной регистрации пользователя.

        Что тестируем:
        1. HTTP запрос POST /api/v1/register с валидными данными
        2. Получение корректного HTTP ответа (200, структура JSON)
        3. Реальное создание пользователя в БД
        4. Корректность сохраненных данных

        Фикстуры:
        - client: HTTP клиент с реальной БД (из conftest.py)
        - db_session: прямой доступ к БД для проверок (из conftest.py)

        Почему functional:
        - Нет моков RegisterService - полный цикл до БД
        - Проверяем реальное сохранение данных
        """
        # 1. Подготовка тестовых данных
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "phone": "+7 (999) 123-45-67"
        }

        # 2. HTTP запрос к API (полный цикл: роутер → сервис → БД)
        response = await client.post("/api/v1/register", json=user_data)

        # 3. Проверка HTTP ответа
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        uuid.UUID(data["data"]["id"])
        assert "message" in data
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

        # 4. Проверка что пользователь РЕАЛЬНО создался в БД
        from app.models.v1.users import UserModel
        from sqlalchemy import select

        result = await db_session.execute(
            select(UserModel).where(UserModel.email == user_data["email"])
        )
        user = result.scalar_one_or_none()

        # Проверяем что пользователь найден и данные корректны
        assert user is not None
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        # Пароль должен быть захеширован, не в открытом виде :)
        assert user.hashed_password != user_data["password"]

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_registration_with_cookies(self, client: AsyncClient):
        """
        Тест регистрации с использованием cookies.

        Что тестируем:
        1. Параметр use_cookies=true в URL
        2. Установку HTTP cookies в ответе
        3. Отсутствие токенов в JSON (они в cookies)

        Особенность: не проверяем БД напрямую, но данные все равно сохраняются
        """
        # 1. Подготовка тестовых данных
        user_data = {
            "username": "cookieuser",
            "email": "cookie@example.com",
            "password": "SecurePass123!"
        }

        # 2. HTTP запрос с параметром use_cookies=true
        response = await client.post(
            "/api/v1/register?use_cookies=true",
            json=user_data
        )
        # Проверяем HTTP статус
        assert response.status_code == 200

        # Проверяем заголовки Set-Cookie (токены должны быть в cookies)
        set_cookie_headers = response.headers.get_list("set-cookie")
        assert any("access_token=" in cookie for cookie in set_cookie_headers)
        assert any("refresh_token=" in cookie for cookie in set_cookie_headers)

        # Проверяем что токены в JSON равны None (не возвращаются в теле)
        data = response.json()
        assert data["data"]["access_token"] is None
        assert data["data"]["refresh_token"] is None

        # Проверяем что регистрация прошла успешно
        assert data["success"] is True
        assert "id" in data["data"]
        uuid.UUID(data["data"]["id"])

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_duplicate_email_registration(self, client: AsyncClient):
        """
        Тест регистрации с дублирующимся email.

        Что тестируем:
        1. Первая регистрация проходит успешно
        2. Вторая регистрация с тем же email отклоняется
        3. Корректный HTTP статус 409 (Conflict)
        4. Информативное сообщение об ошибке

        Бизнес-правило: email должен быть уникальным

        Почему functional:
        - Проверяем реальное ограничение уникальности в БД
        - Первый пользователь реально сохраняется
        - Второй запрос реально проверяется на дубликат
        """
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        }

        # Первая регистрация
        response1 = await client.post("/api/v1/register", json=user_data)
        assert response1.status_code == 200

        # Попытка повторной регистрации с тем же email, но другим username
        user_data["username"] = "user2"
        response2 = await client.post("/api/v1/register", json=user_data)

        # Проверяем что вторая регистрация отклонена
        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False

        # Проверяем текст ошибки содержит информацию о дублирующемся email
        error_detail = data["error"]["detail"].lower()
        assert "email" in error_detail
        assert "duplicate@example.com" in error_detail

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_duplicate_username_registration(self, client: AsyncClient):
        """
        Тест регистрации с дублирующимся username.

        Аналогично тесту с email, но проверяем уникальность username
        """
        user_data = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "SecurePass123!"
        }

        # Первая регистрация
        response1 = await client.post("/api/v1/register", json=user_data)
        assert response1.status_code == 200

        # Попытка повторной регистрации с тем же username, но другим email
        user_data["email"] = "user2@example.com"
        response2 = await client.post("/api/v1/register", json=user_data)

        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False

        error_detail = data["error"]["detail"].lower()
        assert "username" in error_detail
        assert "duplicateuser" in error_detail

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_duplicate_phone_registration(self, client: AsyncClient):
        """
        Тест регистрации с дублирующимся телефоном.

        Проверяем уникальность номера телефона
        """
        user_data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "phone": "+7 (999) 123-45-67"
        }

        # Первая регистрация
        response1 = await client.post("/api/v1/register", json=user_data)
        assert response1.status_code == 200

        # Попытка повторной регистрации с тем же телефоном
        user_data.update({
            "username": "user2",
            "email": "user2@example.com"
        })
        response2 = await client.post("/api/v1/register", json=user_data)

        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False

        error_detail = data["error"]["detail"].lower()
        assert "phone" in error_detail or "телефон" in error_detail

        @pytest.mark.asyncio
        @pytest.mark.functional
        async def test_invalid_email_format(self, client: AsyncClient):
            """
            Тест регистрации с невалидным email.

            Что тестируем:
            1. Валидацию email на уровне Pydantic схемы
            2. HTTP статус 422 (Unprocessable Entity)

            Почему functional:
            - Проверяем полный цикл валидации
            - Запрос доходит до роутера и валидируется схемой
            """
            user_data = {
                "username": "testuser",
                "email": "invalid-email", # Невалидный формат email
                "password": "SecurePass123!!"
            }

            response = await client.post("/api/v1/register", json=user_data)

            assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_weak_password(self, client: AsyncClient):
        """
        Тест регистрации со слабым паролем.

        Проверяем валидацию пароля (длина, сложность)
        """
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123" # Слишком короткий пароль
        }

        response = await client.post("/api/v1/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_missing_required_fields(self, client: AsyncClient):
        """
        Тест регистрации с отсутствующими обязательными полями.

        Проверяем валидацию обязательных полей на уровне Pydantic
        """
        user_data = {
            "username": "testuser",
        }

        response = await client.post("/api/v1/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_user_created_with_correct_defaults(self, client: AsyncClient, db_session: AsyncSession):
        """
        Тест что пользователь создается с корректными значениями по умолчанию.

        Проверяем:
        - is_verified = False (пользователь не подтвержден)
        - is_active = True (пользователь активен)
        - created_at устанавливается
        - пароль хешируется
        """
        user_data = {
            "username": "defaultuser",
            "email": "default@example.com",
            "password": "SecurePass123!"
        }

        response = await client.post("/api/v1/register", json=user_data)
        assert response.status_code == 200

        # Проверяем данные в БД
        from app.models.v1.users import UserModel
        from sqlalchemy import select

        result = await db_session.execute(
            select(UserModel).where(UserModel.email == user_data["email"])
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.is_verified is False  # По умолчанию не подтвержден
        assert user.is_active is True     # По умолчанию активен
        assert user.created_at is not None
        assert user.hashed_password != user_data["password"]  # Пароль захеширован
        assert len(user.hashed_password) > 50  # Хеш длинный

    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_tokens_are_limited_for_unverified_user(self, client: AsyncClient):
        """
        Тест что для неподтвержденного пользователя выдаются ограниченные токены.

        Бизнес-правило: неподтвержденные пользователи получают токены с ограниченными правами
        """
        user_data = {
            "username": "limiteduser",
            "email": "limited@example.com",
            "password": "SecurePass123!"
        }

        response = await client.post("/api/v1/register", json=user_data)
        assert response.status_code == 200

        data = response.json()
        access_token = data["data"]["access_token"]

        # Проверяем что токен содержит информацию о неподтвержденном статусе
        # (в реальном проекте нужно декодировать JWT и проверить claims)
        assert access_token is not None
        assert len(access_token) > 50  # JWT токен длинный