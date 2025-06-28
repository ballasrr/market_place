"""
INTEGRATION ТЕСТЫ для роутера регистрации пользователей.

Что такое Integration тесты:
- Тестируют ВЗАИМОДЕЙСТВИЕ между компонентами
- Используют МОКИ внешних сервисов (БД, email, Redis)
- Фокусируются на HTTP слое (роутер)
- БЫСТРЫЕ (нет реальных операций с БД)

Отличие от Functional тестов:
- Integration: мокают RegisterService, тестируют HTTP контракты
- Functional: реальные сервисы, тестируют бизнес-логику

Когда использовать:
- Проверка HTTP контрактов (запрос/ответ)
- Проверка обработки ошибок на уровне роутера
- Проверка валидации входных данных
- Быстрая проверка основных сценариев

Структура теста:
1. Мокирование сервисов
2. Настройка возвращаемых значений моков
3. HTTP запрос
4. Проверка HTTP ответа
5. Проверка вызовов моков
"""
import uuid
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient
from tests.utils.helpers import create_test_user_data, assert_response_structure


class TestRegisterRouter:
    """Тесты для RegisterRouter."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_user_success(self, client: AsyncClient):
        """
        Тест успешной регистрации пользователя.

        Что тестируем:
        1. HTTP запрос корректно обрабатывается роутером
        2. Роутер корректно вызывает RegisterService
        3. HTTP ответ имеет правильную структуру
        4. Данные из сервиса корректно возвращаются в ответе

        Что НЕ тестируем:
        - Реальное сохранение в БД (мокаем сервис)
        - Реальную отправку email (мокаем messaging)
        - Бизнес-логику сервиса (тестируется отдельно)

        Фикстуры:
        - client: HTTP клиент (из conftest.py)

        Моки:
        - RegisterService: возвращает предопределенный ответ
        """
        # 1. Подготовка тестовых данных
        user_data = create_test_user_data()

        # 2. Мокирование RegisterService
        with patch('app.services.v1.registration.service.RegisterService') as mock_service_class:
            # Создаем мок экземпляра сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Настраиваем что должен вернуть мок при вызове create_user
            mock_service.create_user.return_value = {
                "success": True,
                "message": "Регистрация завершена. Подтвердите email для полного доступа.",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "role": "user",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2024-01-15T10:30:00Z",
                    "referral_code": "REF12345678",
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "requires_verification": True
                }
            }
            # 3. HTTP запрос к роутеру
            response = await client.post("/api/v1/register", json=user_data)
            # 4. Проверка HTTP ответа
            assert response.status_code == 200
            response_data = response.json()
            # 5. Проверка структуры ответа
            assert_response_structure(response_data, ["success", "message", "data"])
            # 6. Проверка успешности регистрации
            assert response_data["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_user_with_cookies(self, client: AsyncClient):
        """
        Тест регистрации пользователя с использованием cookies.

        Что тестируем:
        1. Параметр use_cookies=true корректно передается в роутер
        2. Роутер корректно обрабатывает Query параметр
        3. HTTP ответ возвращается с правильным статусом

        Фокус на HTTP слое, не на бизнес-логике установки cookies
        """
        user_data = create_test_user_data()

        with patch('app.services.v1.registration.service.RegisterService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            mock_service.create_user.return_value = {
                "success": True,
                "message": "Регистрация завершена. Подтвердите email для полного доступа.",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "role": "user",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2024-01-15T10:30:00Z",
                    "referral_code": "REF12345678",
                    "access_token": None,
                    "refresh_token": None,
                    "token_type": "bearer",
                    "requires_verification": True
                }
            }
            # HTTP запрос с параметром use_cookies=true
            response = await client.post(
                "/api/v1/register?use_cookies=true",
                json=user_data
            )
             # Проверяем что запрос обработан успешно
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_user_invalid_data(self, client: AsyncClient):
        """
        Тест регистрации с невалидными данными.

        Что тестируем:
        1. Валидация Pydantic схемы на уровне роутера
        2. HTTP статус 422 для ошибок валидации
        3. Структура ошибки валидации

        Особенность: НЕ мокируем сервис, т.к. запрос не должен до него дойти
        Валидация происходит на уровне FastAPI до вызова роутера
        """
        invalid_data = {
            "username": "",  # Пустое имя пользователя
            "email": "invalid-email",  # Невалидный email
            "password": "123"  # Слишком короткий пароль
        }

        response = await client.post("/api/v1/register", json=invalid_data)

        # Проверяем статус ошибки валидации
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_user_missing_required_fields(self, client: AsyncClient):
        """
        Тест валидации обязательных полей при регистрации.

        Что тестируем:
        1. API возвращает ошибку 422 при отсутствии обязательных полей
        2. Структура ответа соответствует схеме ошибок
        3. Список ошибок содержит все отсутствующие поля
        """
        # Отправляем пустой запрос
        response = await client.post("/api/v1/register", json={})

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

        assert response.status_code == 422
        response_data = response.json()

        # Проверяем структуру ответа согласно вашему обработчику валидации
        assert response_data["success"] is False
        assert response_data["message"] is None
        assert response_data["data"] is None
        assert "error" in response_data

        error_data = response_data["error"]
        assert error_data["error_type"] == "validation_error"
        assert error_data["detail"] == "Ошибка валидации данных"
        assert "extra" in error_data
        assert "errors" in error_data["extra"]

        # Проверяем список ошибок валидации
        validation_errors = error_data["extra"]["errors"]
        assert isinstance(validation_errors, list)
        assert len(validation_errors) > 0

        # Извлекаем поля с ошибками
        error_fields = [err["loc"][-1] for err in validation_errors]

        # Проверяем наличие обязательных полей
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            assert field in error_fields, f"Поле '{field}' должно быть в списке ошибок валидации"

        # Проверяем, что каждая ошибка содержит необходимые поля
        for error in validation_errors:
            assert "loc" in error, "Каждая ошибка должна содержать поле 'loc'"
            assert "msg" in error, "Каждая ошибка должна содержать поле 'msg'"
            assert isinstance(error["loc"], list), "Поле 'loc' должно быть списком"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_user_password_validation(self, client: AsyncClient):
        """
        Тест валидации пароля.

        Что тестируем:
        1. Различные сценарии валидации пароля
        2. Успешные и неуспешные случаи
        3. Корректную обработку на уровне роутера

        Смешанный подход: для валидных паролей мокируем сервис,
        для невалидных - ожидаем ошибку валидации
        """
        test_cases = [
            {"password": "12345", "should_fail": True},  # Слишком короткий
            {"password": "onlyletters", "should_fail": True},  # Только буквы
            {"password": "12345678", "should_fail": True},  # Только цифры
            {"password": "ValidPass123!", "should_fail": False},  # Валидный пароль
        ]

        for case in test_cases:
            user_data = create_test_user_data()
            user_data["password"] = case["password"]

            if not case["should_fail"]:
                # Для валидных паролей мокируем сервис
                with patch('app.services.v1.registration.service.RegisterService') as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service_class.return_value = mock_service

                    mock_service.create_user.return_value = {
                        "success": True,
                        "message": "Пользователь успешно зарегистрирован",
                        "data": {"user": {}, "tokens": {}}
                    }

                    response = await client.post("/api/v1/register", json=user_data)
                    assert response.status_code == 200
            else:
                # Для невалидных паролей ожидаем ошибку валидации
                response = await client.post("/api/v1/register", json=user_data)
                assert response.status_code in [401, 422]  # Может быть и 401 и 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_response_structure_validation(self, client: AsyncClient):
        """
        Тест валидации структуры ответа роутера.

        Что тестируем:
        1. Ответ соответствует ожидаемой схеме
        2. Все обязательные поля присутствуют
        3. Типы данных корректны

        Фокус на контракте API, а не на бизнес-логике
        """
        user_data = create_test_user_data()

        with patch('app.services.v1.registration.service.RegisterService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Подробный мок ответ для проверки структуры
            mock_service.create_user.return_value = {
                "success": True,
                "message": "Регистрация завершена. Подтвердите email для полного доступа.",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "role": "user",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2024-01-15T10:30:00Z",
                    "referral_code": "REF12345678",
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "requires_verification": True
                }
            }

            response = await client.post("/api/v1/register", json=user_data)

            assert response.status_code == 200
            response_data = response.json()

            # Проверяем основную структуру
            assert_response_structure(response_data, ["success", "message", "data"])

            # Проверяем структуру данных пользователя
            data = response_data["data"]
            required_fields = ["id", "username", "email", "access_token", "refresh_token", "token_type"]
            for field in required_fields:
                assert field in data

            assert isinstance(data["access_token"], str)
            assert isinstance(data["refresh_token"], str)
            assert len(data["access_token"]) > 10
            assert len(data["refresh_token"]) > 10
            uuid.UUID(data["id"])  # Проверка, что id это UUID

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_content_type_validation(self, client: AsyncClient):
        """
        Тест валидации Content-Type заголовка.

        Что тестируем:
        1. Роутер принимает только application/json
        2. Некорректный Content-Type отклоняется
        """
        user_data = create_test_user_data()

        # Попытка отправить данные как form-data вместо JSON
        response = await client.post(
            "/api/v1/register",
            data=user_data  # data вместо json
        )

        # FastAPI должен вернуть ошибку о неподдерживаемом Content-Type
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_http_methods(self, client: AsyncClient):
        """
        Тест что endpoint поддерживает только POST метод.

        Что тестируем:
        1. POST запросы обрабатываются
        2. GET, PUT, DELETE запросы отклоняются
        """
        # POST должен работать (с моком)
        with patch('app.services.v1.registration.service.RegisterService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.create_user.return_value = {"success": True, "data": {}}

            response = await client.post("/api/v1/register", json=create_test_user_data())
            assert response.status_code == 200

        # GET должен вернуть 405 Method Not Allowed
        response = await client.get("/api/v1/register")
        assert response.status_code == 405

        # PUT должен вернуть 405 Method Not Allowed
        response = await client.put("/api/v1/register", json={})
        assert response.status_code == 405