"""
Модуль для работы с базой данных.

Предоставляет DatabaseClient для управления подключением к PostgreSQL через SQLAlchemy
с использованием глобальной фабрики сессий для оптимальной производительности.
"""

from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.connections import BaseClient
from app.core.settings import Config, settings


class DatabaseClient(BaseClient):
    """
    Клиент для работы с базой данных.

    Управляет глобальной фабрикой сессий и пулом подключений.
    Реализует паттерн Singleton для engine и session_factory.
    """

    # Глобальные переменные класса
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    def __init__(self, config: Config = settings) -> None:
        super().__init__()
        self._config = config

    async def connect(self) -> async_sessionmaker[AsyncSession]:
        """
        Создает глобальную фабрику сессий (если еще не создана).

        Returns:
            async_sessionmaker: Фабрика для создания сессий

        Raises:
            SQLAlchemyError: При ошибке подключения к базе данных
        """
        if self._session_factory is not None:
            self.logger.debug("Фабрика сессий уже инициализирована")
            return self._session_factory

        try:
            self.logger.info("Инициализация подключения к базе данных...")

            self._engine = create_async_engine(
                url=self._config.database_url, **self._config.engine_params
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine, **self._config.session_params
            )

            self.logger.info("Подключение к базе данных успешно инициализировано")
            return self._session_factory

        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    async def close(self) -> None:
        """
        Закрывает подключение к базе данных.

        Безопасно закрывает все соединения в пуле и освобождает ресурсы.
        """
        if self._engine:
            self.logger.info("Закрытие подключения к базе данных...")
            await self._engine.dispose()
            DatabaseClient._engine = None
            DatabaseClient._session_factory = None
            self.logger.info("Подключение к базе данных закрыто")

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Получение фабрики сессий.

        Returns:
            async_sessionmaker: Фабрика для создания сессий

        Raises:
            RuntimeError: Если база данных не была инициализирована
        """
        if self._session_factory is None:
            raise RuntimeError(
                "База данных не инициализирована. "
                "Вызовите connect() перед использованием."
            )
        return self._session_factory

    def get_engine(self) -> AsyncEngine:
        """
        Получение текущего движка базы данных.

        Returns:
            AsyncEngine: асинхронный движок SQLAlchemy

        Raises:
            RuntimeError: если движок еще не инициализирован (connect не вызывался)
        """
        self._engine = create_async_engine(
            url=self._config.database_url, **self._config.engine_params
        )

        if self._engine is None:
            raise RuntimeError(
                "База данных не инициализирована. "
                "Вызовите connect() перед использованием."
            )
        return self._engine


# Глобальный экземпляр клиента
database_client = DatabaseClient()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных в FastAPI.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy

    Usage:
        ```python
        @router.post("/users/")
        async def create_user(
            user_data: UserCreate,
            session: AsyncSession = Depends(get_db_session)
        ):
            # Работа с сессией
        ```
    """
    session_factory = database_client.get_session_factory()

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
