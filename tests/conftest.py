"""
Конфигурация для тестов pytest.

Этот файл содержит фикстуры (fixtures) - переиспользуемые компоненты для тестов.
Фикстуры автоматически подставляются в тесты как параметры функций.

Структура тестирования:
- Unit тесты: изолированное тестирование функций/классов с моками
- Integration тесты: тестирование взаимодействия компонентов с моками внешних сервисов
- Functional тесты: тестирование полного цикла с реальной БД
- E2E тесты: тестирование пользовательских сценариев
"""
import uuid
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.dependencies import get_db_session
from app.core.security.auth import get_current_user
from app.core.settings import settings
from app.main import app
from app.models.v1.base import BaseModel
from app.models.v1.users import UserRole
from app.schemas import CurrentUserSchema


@pytest_asyncio.fixture
async def test_engine():
    """
    Фикстура для создания тестового движка базы данных.

    Что делает:
    1. Создает отдельную тестовую БД (gidrator_db_test)
    2. Создает все таблицы из моделей SQLAlchemy
    3. После тестов удаляет тестовую БД

    Используется в: db_session фикстуре

    Важно: Использует реальный PostgreSQL, но отдельную БД для тестов!
    """
    # Имя тестовой БД = основная БД + "_test"
    test_db_name = f"{settings.POSTGRES_DB}_test"

    # Подключаемся к PostgreSQL для создания тестовой БД
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD.get_secret_value(),
        database="postgres",  # Подключаемся к системной БД
    )

    try:
        # Удаляем тестовую БД если существует (очистка)
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
        # Создаем новую тестовую БД
        await conn.execute(f'CREATE DATABASE "{test_db_name}"')
    finally:
        await conn.close()

    # Создаем URL для подключения к тестовой БД
    test_db_url = settings.database_url.replace(settings.POSTGRES_DB, test_db_name)

    # Создаем движок SQLAlchemy для тестовой БД
    engine = create_async_engine(
        test_db_url,
        echo=False,  # Не выводить SQL запросы в консоль
        poolclass=NullPool,  # Отключаем connection pool для тестов
    )

    # Создаем все таблицы из моделей SQLAlchemy
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Возвращаем движок для использования в тестах
    yield engine

    # Cleanup: закрываем движок
    await engine.dispose()

    # Удаляем тестовую БД после всех тестов
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD.get_secret_value(),
        database="postgres",
    )
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Фикстура для создания изолированной сессии БД для каждого теста.

    Что делает:
    1. Создает подключение к тестовой БД
    2. Начинает транзакцию
    3. Создает сессию SQLAlchemy
    4. После теста откатывает транзакцию (rollback)

    Изоляция тестов: каждый тест получает чистую БД благодаря rollback

    Используется в: functional тестах для прямого обращения к БД

    Пример использования:
    async def test_user_creation(db_session):
        user = UserModel(username="test", email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        # Проверяем что пользователь создался
    """
    # Создаем подключение к БД
    connection = await test_engine.connect()
    # Начинаем транзакцию
    transaction = await connection.begin()

    # Создаем сессию SQLAlchemy привязанную к этому подключению
    session = AsyncSession(
        bind=connection, expire_on_commit=False  # Не сбрасывать объекты после commit
    )

    try:
        # Возвращаем сессию для использования в тесте
        yield session
    finally:
        # Cleanup: закрываем сессию
        await session.close()
        # Откатываем транзакцию (все изменения теста удаляются!)
        await transaction.rollback()
        # Закрываем подключение
        await connection.close()


@pytest_asyncio.fixture
async def mock_user():
    """
    Фикстура для создания мокового пользователя.

    Используется в: auth_client фикстуре для имитации авторизованного пользователя

    Возвращает: CurrentUserSchema с тестовыми данными пользователя
    """
    return CurrentUserSchema(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )


@pytest_asyncio.fixture(autouse=True)
async def mock_messaging():
    """
    Фикстура для мокирования системы сообщений (RabbitMQ).

    autouse=True: автоматически применяется ко всем тестам

    Что делает:
    - Мокает отправку сообщений в очереди (например, email верификации)
    - Предотвращает реальную отправку email в тестах

    Без этого мока тесты пытались бы отправлять реальные email!
    """
    with patch(
        "app.core.integrations.messaging.producers.broker.publish"
    ) as mock_publish:
        mock_publish.return_value = AsyncMock()
        yield mock_publish


@pytest_asyncio.fixture
async def client(db_session):
    """
    Фикстура для создания HTTP клиента для тестов.

    Что делает:
    1. Подменяет зависимость get_db_session на тестовую сессию
    2. Создает HTTP клиент для отправки запросов к API
    3. После тестов очищает подмены зависимостей

    Используется в: functional тестах для отправки HTTP запросов

    ВАЖНО: Этот клиент использует РЕАЛЬНУЮ БД (через db_session)!

    Пример использования:
    async def test_registration(client):
        response = await client.post("/api/v1/register", json={...})
        assert response.status_code == 200
    """
    # Функция-заменитель для get_db_session зависимости
    async def override_get_db():
        yield db_session  # Возвращаем тестовую сессию вместо продакшн

    # Подменяем зависимость в FastAPI приложении
    app.dependency_overrides[get_db_session] = override_get_db

    try:
        # Создаем HTTP клиент для тестирования FastAPI приложения
        async with AsyncClient(
            transport=ASGITransport(app=app),  # Используем ASGI транспорт
            base_url="http://testserver",  # Базовый URL для запросов
        ) as ac:
            yield ac  # Возвращаем клиент для использования в тестах
    finally:
        # Cleanup: очищаем все подмены зависимостей
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client, mock_user):
    """
    Фикстура для создания HTTP клиента с мокированной авторизацией.

    Что делает:
    1. Подменяет get_current_user зависимость на mock_user
    2. Все запросы через этот клиент будут "авторизованы"
    3. После тестов очищает подмену

    Используется в: тестах защищенных endpoints (требующих авторизации)

    Пример использования:
    async def test_get_users(auth_client):
        # Этот запрос будет выполнен от имени mock_user
        response = await auth_client.get("/api/v1/users")
        assert response.status_code == 200
    """
    # Функция-заменитель для get_current_user зависимости
    async def mock_get_current_user():
        return mock_user  # Возвращаем мокового пользователя

    # Подменяем зависимость авторизации
    app.dependency_overrides[get_current_user] = mock_get_current_user

    try:
        yield client  # Возвращаем тот же HTTP клиент, но с мокированной авторизацией
    finally:
        # Cleanup: удаляем подмену авторизации
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
