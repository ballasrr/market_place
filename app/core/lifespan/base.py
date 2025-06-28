"""
Модуль управления жизненным циклом FastAPI приложения.

Предоставляет централизованную систему для регистрации и выполнения обработчиков
событий запуска и остановки приложения. Использует паттерн Registry для
автоматического обнаружения и регистрации обработчиков из различных модулей.

Основные компоненты:
- Регистрация обработчиков через декораторы
- Автоматическое выполнение всех зарегистрированных обработчиков
- Централизованное логирование событий жизненного цикла
- Обработка ошибок в обработчиках без остановки приложения

Usage:
    ```python
    # В модуле с обработчиками
    @register_startup_handler
    async def my_startup_handler(app: FastAPI):
        # Логика инициализации
        pass

    # В settings.py
    from app.core.lifespan import lifespan

    @property
    def app_params(self) -> dict:
        return {
            # Другие параметры FastAPI
            "lifespan": lifespan,
        }
    ```
"""

import logging
from contextlib import asynccontextmanager
from typing import Awaitable, Callable, List

from fastapi import FastAPI

logger = logging.getLogger("app.lifecycle")

# Типы для инициализаторов и деструкторов
StartupHandler = Callable[[FastAPI], Awaitable[None]]
"""Тип функции-обработчика события запуска приложения."""

ShutdownHandler = Callable[[FastAPI], Awaitable[None]]
"""Тип функции-обработчика события остановки приложения."""

# Списки обработчиков
startup_handlers: List[StartupHandler] = []
"""Глобальный реестр обработчиков запуска приложения."""

shutdown_handlers: List[ShutdownHandler] = []
"""Глобальный реестр обработчиков остановки приложения."""


def register_startup_handler(handler: StartupHandler):
    """
    Декоратор для регистрации обработчика события запуска приложения.

    Автоматически добавляет функцию в глобальный реестр обработчиков запуска.
    Обработчики выполняются в порядке регистрации при старте приложения.

    Args:
        handler: Асинхронная функция-обработчик, принимающая экземпляр FastAPI

    Returns:
        StartupHandler: Исходная функция-обработчик (для возможности цепочки декораторов)

    Example:
        ```python
        @register_startup_handler
        async def initialize_database(app: FastAPI):
            # Инициализация базы данных
            await database.connect()
            app.state.database = database
        ```
    """
    startup_handlers.append(handler)
    return handler


def register_shutdown_handler(handler: ShutdownHandler):
    """
    Декоратор для регистрации обработчика события остановки приложения.

    Автоматически добавляет функцию в глобальный реестр обработчиков остановки.
    Обработчики выполняются в порядке регистрации при остановке приложения.

    Args:
        handler: Асинхронная функция-обработчик, принимающая экземпляр FastAPI

    Returns:
        ShutdownHandler: Исходная функция-обработчик (для возможности цепочки декораторов)

    Example:
        ```python
        @register_shutdown_handler
        async def close_database(app: FastAPI):
            # Закрытие подключения к базе данных
            if hasattr(app.state, 'database'):
                await app.state.database.close()
        ```
    """
    shutdown_handlers.append(handler)
    return handler


async def run_startup_handlers(app: FastAPI):
    """
    Выполняет все зарегистрированные обработчики запуска приложения.

    Автоматически импортирует и регистрирует обработчики из известных модулей,
    затем последовательно выполняет все зарегистрированные обработчики.
    При возникновении ошибки в любом обработчике, она логируется, но выполнение
    продолжается для остальных обработчиков.

    Args:
        app: Экземпляр FastAPI приложения

    Note:
        Обработчики выполняются в порядке их регистрации. Если порядок выполнения
        критичен, убедитесь, что модули импортируются в правильной последовательности.

    Example:
        ```python
        # Обычно вызывается автоматически через lifespan
        await run_startup_handlers(app)
        ```
    """

    from app.core.lifespan.clients import initialize_clients
    from app.core.lifespan.database import initialize_database

    # Добавляем обработчики если их нет (защита от дублирования)
    if initialize_database not in startup_handlers:
        startup_handlers.append(initialize_database)
    if initialize_clients not in startup_handlers:
        startup_handlers.append(initialize_clients)
    # Выполняем все зарегистрированные обработчики
    for handler in startup_handlers:
        try:
            logger.info("Запуск обработчика: %s", handler.__name__)
            await handler(app)
            logger.debug("Обработчик %s выполнен успешно", handler.__name__)
        except Exception as e:
            logger.error("Ошибка в обработчике %s: %s", handler.__name__, str(e))
            # Продолжаем выполнение остальных обработчиков


async def run_shutdown_handlers(app: FastAPI):
    """
    Выполняет все зарегистрированные обработчики остановки приложения.

    Автоматически импортирует и регистрирует обработчики из известных модулей,
    затем последовательно выполняет все зарегистрированные обработчики.
    При возникновении ошибки в любом обработчике, она логируется, но выполнение
    продолжается для остальных обработчиков.

    Args:
        app: Экземпляр FastAPI приложения

    Note:
        Обработчики выполняются в порядке их регистрации. Рекомендуется
        регистрировать обработчики закрытия в обратном порядке относительно
        обработчиков инициализации.

    Example:
        ```python
        # Обычно вызывается автоматически через lifespan
        await run_shutdown_handlers(app)
        ```
    """
    from app.core.lifespan.clients import close_clients
    from app.core.lifespan.database import close_database_connection

    # Добавляем обработчики если их нет (защита от дублирования)
    if close_database_connection not in shutdown_handlers:
        shutdown_handlers.append(close_database_connection)
    if close_clients not in shutdown_handlers:
        shutdown_handlers.append(close_clients)

    # Выполняем все зарегистрированные обработчики
    for handler in shutdown_handlers:
        try:
            logger.info("Запуск обработчика остановки: %s", handler.__name__)
            await handler(app)
            logger.debug("Обработчик остановки %s выполнен успешно", handler.__name__)
        except Exception as e:
            logger.error(
                "Ошибка в обработчике остановки %s: %s", handler.__name__, str(e)
            )
            # Продолжаем выполнение остальных обработчиков


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла FastAPI приложения.

    Управляет полным жизненным циклом приложения, автоматически выполняя
    все зарегистрированные обработчики запуска при старте и обработчики
    остановки при завершении работы приложения.

    Args:
        app: Экземпляр FastAPI приложения

    Yields:
        None: Контроль передается приложению для обработки запросов

    Usage:
        ```python
        from app.core.lifespan.base import lifespan

        app = FastAPI(
            title="My API",
            lifespan=lifespan
        )
        ```

    Note:
        Этот контекстный менеджер должен быть передан в параметр lifespan
        при создании экземпляра FastAPI. Он заменяет устаревшие события
        startup и shutdown в FastAPI.

    Example:
        ```python
        # main.py
        from fastapi import FastAPI
        from app.core.lifespan.base import lifespan

        # Создание приложения с автоматическим управлением жизненным циклом
        app = FastAPI(
            title="Gidrator API",
            version="1.0.0",
            lifespan=lifespan
        )

        # Все обработчики запуска и остановки будут выполнены автоматически
        ```
    """
    # Фаза запуска: выполняем все обработчики инициализации
    logger.info("Начало инициализации приложения")
    await run_startup_handlers(app)
    logger.info("Инициализация приложения завершена")

    # Передаем управление приложению для обработки запросов
    yield

    # Фаза остановки: выполняем все обработчики завершения
    logger.info("Начало завершения работы приложения")
    await run_shutdown_handlers(app)
    logger.info("Завершение работы приложения выполнено")
