"""
Модуль аутентификации и авторизации пользователей.

Предоставляет компоненты для проверки подлинности и авторизации
пользователей в приложении FastAPI с использованием JWT токенов.

Основные компоненты:
- OAuth2PasswordBearer: схема безопасности для документации OpenAPI
- get_current_user: функция-зависимость для получения текущего пользователя

Примеры использования:
    ```python
    @router.get("/protected")
    async def protected_route(
        user: CurrentUserSchema = Depends(get_current_user)
    ):
        return {"message": f"Hello, {user.username}!"}
    ```
"""

import logging

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.core.exceptions import (InvalidCredentialsError, TokenError,
                                 TokenInvalidError, TokenMissingError)
from app.core.security.token import TokenManager
from app.core.settings import settings
from app.schemas import CurrentUserSchema, UserCredentialsSchema
from app.services.v1.users.data_manager import UserDataManager

logger = logging.getLogger(__name__)

# Создаем экземпляр OAuth2PasswordBearer для использования с Depends
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.AUTH_URL,
    scheme_name="OAuth2PasswordBearer",
    description="Bearer token",
    auto_error=False,
)


class AuthenticationManager:
    """
    Менеджер аутентификации пользователей.

    Предоставляет методы для работы с аутентификацией,
    включая проверку токенов и получение данных текущего пользователя.

    Methods:
        get_current_user: Получает данные текущего пользователя по токену
        validate_token: Проверяет валидность токена и извлекает полезную нагрузку
    """

    @staticmethod
    async def get_current_user(
        request: Request,
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db_session),
    ) -> CurrentUserSchema:
        """
        Получает данные текущего аутентифицированного пользователя.

        Проверяет JWT токен, переданный в заголовке Authorization,
        декодирует его, и получает пользователя из системы по идентификатору
        в токене (sub).

        Args:
            request: Запрос FastAPI, содержащий заголовки HTTP
            token: Токен доступа, извлекаемый из заголовка Authorization
            session: Сессия базы данных

        Returns:
            CurrentUserSchema: Схема данных текущего пользователя

        Raises:
            TokenInvalidError: Если токен отсутствует, недействителен или истек
            InvalidCredentialsError: Если пользователь не найден
        """
        logger.debug(
            "Обработка запроса аутентификации с заголовками: %s", request.headers
        )
        logger.debug("Начало получения данных пользователя")
        logger.debug("Получен токен: %s", token)

        if not token:
            logger.debug("Токен отсутствует в запросе")
            raise TokenMissingError()

        try:
            # Проверяем и декодируем токен
            payload = TokenManager.verify_token(token)
            user_email = TokenManager.validate_payload(payload)

            # Получаем пользователя через UserDataManager
            user_manager = UserDataManager(session)
            user = await user_manager.get_user_by_identifier(user_email)

            if not user:
                logger.debug("Пользователь с email %s не найден", user_email)
                raise InvalidCredentialsError()

            # Преобразуем в схему учетных данных
            user_schema = UserCredentialsSchema.model_validate(user)
            logger.debug("Пользователь успешно аутентифицирован: %s", user_schema)

            # Создаем схему текущего пользователя
            current_user = CurrentUserSchema(
                id=user_schema.id,
                username=user_schema.username,
                email=user_schema.email,
                role=user_schema.role,
                is_active=user_schema.is_active,
                is_verified=user_schema.is_verified,
            )

            return current_user

        except TokenError:
            # Перехватываем все ошибки токенов и пробрасываем дальше
            raise
        except Exception as e:
            logger.debug("Ошибка при аутентификации: %s", str(e))
            raise TokenInvalidError() from e


# Создаем функцию-зависимость для использования в роутерах
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUserSchema:
    """
    Функция-зависимость для получения текущего пользователя.

    Используется в роутерах FastAPI для автоматической аутентификации.

    Args:
        request: HTTP запрос
        token: JWT токен из заголовка Authorization
        session: Сессия базы данных

    Returns:
        CurrentUserSchema: Данные текущего пользователя

    Example:
        ```python
        @router.get("/profile")
        async def get_profile(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return {"user": current_user}
        ```
    """
    return await AuthenticationManager.get_current_user(request, token, session)


# Опциональная зависимость для маршрутов, где аутентификация не обязательна
async def get_current_user_optional(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUserSchema | None:
    """
    Опциональная функция-зависимость для получения текущего пользователя.

    Возвращает None если токен отсутствует или невалиден,
    вместо выбрасывания исключения.

    Args:
        request: HTTP запрос
        token: JWT токен из заголовка Authorization (опционально)
        session: Сессия базы данных

    Returns:
        CurrentUserSchema | None: Данные пользователя или None

    Example:
        ```python
        @router.get("/public-content")
        async def get_content(
            current_user: CurrentUserSchema | None = Depends(get_current_user_optional)
        ):
            if current_user:
                return {"message": f"Hello, {current_user.username}!"}
            return {"message": "Hello, anonymous!"}
        ```
    """
    try:
        return await AuthenticationManager.get_current_user(request, token, session)
    except (TokenError, InvalidCredentialsError):
        return None
