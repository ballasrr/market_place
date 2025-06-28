"""
Сервис аутентификации пользователей.

Обеспечивает аутентификацию, создание токенов и управление сессиями.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (ForbiddenError, InvalidCredentialsError,
                                 TokenExpiredError, TokenInvalidError,
                                 UserNotFoundError)
from app.core.integrations.cache.auth import AuthRedisDataManager
from app.core.integrations.mail import AuthEmailDataManager
from app.core.security.cookies import CookieManager
from app.core.security.password import PasswordHasher
from app.core.security.token import TokenManager
from app.core.settings import settings
from app.schemas import (AuthSchema, LogoutDataSchema,  # TokenDataSchema
                         LogoutResponseSchema, PasswordResetConfirmDataSchema,
                         PasswordResetConfirmResponseSchema,
                         PasswordResetConfirmSchema, PasswordResetDataSchema,
                         PasswordResetResponseSchema, TokenResponseSchema,
                         UserCredentialsSchema)
from app.services.v1.base import BaseService

from .data_manager import AuthDataManager


class AuthService(BaseService):
    """
    Сервис для аутентификации пользователей.

    Предоставляет методы для:
    - Аутентификации пользователей
    - Создания и обновления JWT токенов
    - Выхода из системы
    - Восстановления пароля (заглушки)

    Attributes:
        session: Асинхронная сессия базы данных
        data_manager: Менеджер данных для аутентификации
    """

    def __init__(self, session: AsyncSession, redis: Optional[Redis] = None):
        """
        Инициализирует сервис аутентификации.

        Args:
            session: Асинхронная сессия базы данных
        """
        super().__init__(session)
        self.data_manager = AuthDataManager(session)
        self.email_data_manager = AuthEmailDataManager()
        self.redis_data_manager = AuthRedisDataManager(redis) if redis else None

    async def authenticate(
        self,
        form_data: OAuth2PasswordRequestForm,
        response: Optional[Response] = None,
        use_cookies: bool = False,
    ) -> TokenResponseSchema:
        """
        Аутентифицирует пользователя по логину и паролю.

        Args:
            form_data: Данные для аутентификации пользователя
            response: HTTP ответ для установки куков (опционально)
            use_cookies: Использовать ли куки для хранения токенов

        Returns:
            TokenResponseSchema: Токены доступа

        Raises:
            InvalidCredentialsError: Если пользователь не найден или пароль неверный
            ForbiddenError: Если аккаунт деактивирован
        """
        credentials = AuthSchema(
            username=form_data.username, password=form_data.password
        )

        identifier = credentials.username

        self.logger.info(
            "Попытка аутентификации",
            extra={
                "identifier": identifier,
                "has_password": bool(credentials.password),
            },
        )

        # Ищем пользователя по email, телефону или имени пользователя
        user_model = await self.data_manager.get_user_by_identifier(identifier)

        self.logger.info(
            "Начало аутентификации",
            extra={"identifier": identifier, "user_found": bool(user_model)},
        )

        if not user_model:
            self.logger.warning(
                "Пользователь не найден", extra={"identifier": identifier}
            )
            raise InvalidCredentialsError()

        # Проверяем активность аккаунта
        if not user_model.is_active:
            self.logger.warning(
                "Попытка входа в неактивный аккаунт",
                extra={"identifier": identifier, "user_id": user_model.id},
            )
            raise ForbiddenError(
                detail="Аккаунт деактивирован",
                extra={"identifier": credentials.username},
            )

        # Проверяем пароль
        if not PasswordHasher.verify(user_model.hashed_password, credentials.password):
            self.logger.warning(
                "Неверный пароль",
                extra={"identifier": identifier, "user_id": user_model.id},
            )
            raise InvalidCredentialsError()

        # Создаем схему пользователя для токена
        user_schema = UserCredentialsSchema.model_validate(user_model)

        if not user_schema.is_verified:
            self.logger.warning(
                "Вход с неподтвержденным аккаунтом",
                extra={"identifier": identifier, "user_id": user_model.id},
            )

        self.logger.info(
            "Аутентификация успешна",
            extra={
                "user_id": user_schema.id,
                "email": user_schema.email,
                "role": user_schema.role,
            },
        )

        await self.redis_data_manager.set_online_status(user_schema.id, True)
        self.logger.info(
            "Пользователь вошел в систему",
            extra={
                "user_id": user_schema.id,
                "email": user_schema.email,
                "is_online": True,
            },
        )

        await self.data_manager.update_items(
            user_schema.id, {"last_login": datetime.now(timezone.utc)}
        )

        # Создаем токены
        access_token = await self.create_token(user_schema)
        refresh_token = await self.create_refresh_token(user_schema.id)

        # Опционально устанавливаем куки
        if response and use_cookies:
            CookieManager.set_auth_cookies(response, access_token, refresh_token)

            return TokenResponseSchema(
                message="Аутентификация успешна",
                access_token=None,
                refresh_token=None,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        return TokenResponseSchema(
            message="Аутентификация успешна",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def create_token(self, user_schema: UserCredentialsSchema) -> str:
        """
        Создание JWT access токена.

        Args:
            user_schema: Данные пользователя

        Returns:
            str: Access токен
        """
        if user_schema.is_verified:
            access_token = TokenManager.create_full_token(user_schema)
        else:
            access_token = TokenManager.create_limited_token(user_schema)

        self.logger.debug(
            "Сгенерирован токен", extra={"access_token_length": len(access_token)}
        )

        await self.redis_data_manager.save_token(user_schema, access_token)
        self.logger.info(
            "Токен создан и сохранен в Redis",
            extra={"user_id": user_schema.id, "access_token_length": len(access_token)},
        )

        return access_token

    async def create_refresh_token(self, user_id: Union[int, uuid.UUID]) -> str:
        """
        Создание JWT refresh токена.

        Args:
            user_id: ID пользователя

        Returns:
            str: Refresh токен
        """
        refresh_token = TokenManager.create_refresh_token(user_id)

        self.logger.debug(
            "Сгенерирован refresh токен",
            extra={"refresh_token_length": len(refresh_token)},
        )

        await self.redis_data_manager.save_refresh_token(user_id, refresh_token)

        self.logger.info(
            "Refresh токен создан и сохранен в Redis",
            extra={"user_id": str(user_id), "refresh_token_length": len(refresh_token)},
        )

        return refresh_token

    async def refresh_token(
        self,
        refresh_token: str,
        response: Optional[Response] = None,
        use_cookies: bool = False,
    ) -> TokenResponseSchema:
        """
        Обновляет access токен с помощью refresh токена.

        Args:
            refresh_token: Refresh токен

        Returns:
            TokenResponseSchema: Новые токены доступа

        Raises:
            TokenInvalidError: Если refresh токен недействителен
            TokenExpiredError: Если refresh токен истек
            UserNotFoundError: Если пользователь не найден
        """
        try:
            # Декодируем refresh токен
            payload = TokenManager.decode_token(refresh_token)

            # Валидируем refresh токен
            user_id = TokenManager.validate_refresh_token(payload)

            # Проверяем, что refresh токен существует в Redis
            if not await self.redis_data_manager.check_refresh_token(
                user_id, refresh_token
            ):
                self.logger.warning(
                    "Попытка использовать неизвестный refresh токен",
                    extra={"user_id": str(user_id)},
                )
                raise TokenInvalidError()

            # Получаем пользователя
            user_model = await self.data_manager.get_model_by_field("id", user_id)

            if not user_model:
                self.logger.warning(
                    "Пользователь не найден при обновлении токена",
                    extra={"user_id": str(user_id)},
                )
                raise UserNotFoundError(field="id", value=user_id)

            user_schema = UserCredentialsSchema.model_validate(user_model)

            # Создаем новые токены
            access_token = await self.create_token(user_schema)
            new_refresh_token = await self.create_refresh_token(user_id)

            # Удаляем старый refresh токен
            await self.redis_data_manager.remove_refresh_token(user_id, refresh_token)

            self.logger.info(
                "Токены успешно обновлены",
                extra={"user_id": str(user_id)},
            )

            # Опционально обновляем куки
            if response and use_cookies:
                CookieManager.set_auth_cookies(
                    response, access_token, new_refresh_token
                )

                return TokenResponseSchema(
                    message="Токен успешно обновлен",
                    access_token=None,
                    refresh_token=None,
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )

            return TokenResponseSchema(
                message="Токен успешно обновлен",
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        except (TokenExpiredError, TokenInvalidError) as e:
            self.logger.warning(
                "Ошибка при обновлении токена: %s",
                type(e).__name__,
                extra={"error_type": type(e).__name__},
            )
            raise

    async def logout(
        self,
        authorization: Optional[str],
        response: Optional[Response] = None,
        clear_cookies: bool = False,
    ) -> LogoutResponseSchema:
        """
        Выполняет выход пользователя из системы.

        Args:
            access_token: Access токен пользователя

        Returns:
            LogoutResponseSchema: Подтверждение выхода
        """
        try:
            # Извлекаем токен из заголовка
            token = TokenManager.get_token_from_header(authorization)

            try:
                # Получаем данные из токена
                payload = TokenManager.decode_token(token)

                # Получаем user_id пользователя
                user_id_str = payload.get("user_id")

                if user_id_str:
                    user_id = uuid.UUID(user_id_str)
                    await self.redis_data_manager.set_online_status(user_id, False)

                    # Удаляем все refresh токены пользователя
                    await self.redis_data_manager.remove_all_refresh_tokens(user_id)

                    self.logger.debug(
                        "Пользователь вышел из системы, все токены удалены",
                        extra={"user_id": str(user_id), "is_online": False},
                    )

                    # Последнюю активность сохраняем в момент выхода
                    await self.redis_data_manager.update_last_activity(token)

            except (TokenExpiredError, TokenInvalidError) as e:
                # Логируем проблему с токеном, но продолжаем процесс выхода
                self.logger.warning(
                    "Выход с невалидным токеном: %s",
                    type(e).__name__,
                    extra={"token_error": type(e).__name__},
                )

            # Удаляем токен из Redis
            await self.redis_data_manager.remove_token(token)

            logout_data = LogoutDataSchema(logged_out_at=datetime.now(timezone.utc))

            # Опционально очищаем куки
            if response and clear_cookies:
                CookieManager.clear_auth_cookies(response)

            return LogoutResponseSchema(
                message="Выход выполнен успешно", data=logout_data
            )

        except (TokenExpiredError, TokenInvalidError) as e:
            # Для этих ошибок мы не можем продолжить процесс выхода
            self.logger.warning(
                "Ошибка при выходе: %s",
                type(e).__name__,
                extra={"error_type": type(e).__name__},
            )
            # Пробрасываем исключение дальше для обработки на уровне API
            raise

    async def send_password_reset_email(
        self, email: str
    ) -> PasswordResetResponseSchema:
        """
        Отправляет email со ссылкой для сброса пароля

        Args:
            email: Email пользователя

        Returns:
            PasswordResetResponseSchema: Сообщение об успехе

        Raises:
            UserNotFoundError: Если пользователь с указанным email не найден
        """
        self.logger.info("Запрос на сброс пароля", extra={"email": email})

        # Проверяем существование пользователя
        user = await self.data_manager.get_user_by_identifier(email)
        if not user:
            self.logger.warning("Пользователь не найден", extra={"email": email})
            # Не сообщаем об отсутствии пользователя в ответе из соображений безопасности
            return PasswordResetResponseSchema(
                success=True,
                message="Инструкции по сбросу пароля отправлены на ваш email",
            )

        # Генерируем токен для сброса пароля
        reset_token = TokenManager.generate_password_reset_token(user.id)

        try:
            await self.email_data_manager.send_password_reset_email(
                to_email=user.email, user_name=user.username, reset_token=reset_token
            )

            self.logger.info(
                "Письмо для сброса пароля отправлено",
                extra={"user_id": user.id, "email": user.email},
            )

            reset_data = PasswordResetDataSchema(
                email=email, expires_in=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            )

            return PasswordResetResponseSchema(
                message="Инструкции по сбросу пароля отправлены на ваш email",
                data=reset_data,
            )

        except Exception as e:
            self.logger.error(
                "Ошибка при отправке письма сброса пароля: %s",
                e,
                extra={"email": email},
            )
            raise

    async def reset_password(
        self, reset_data: PasswordResetConfirmSchema
    ) -> PasswordResetConfirmResponseSchema:
        """
        Устанавливает новый пароль по токену сброса

        Args:
            token: Токен сброса пароля
            new_password: Новый пароль

        Returns:
            PasswordResetConfirmResponseSchema: Сообщение об успехе

        Raises:
            TokenInvalidError: Если токен недействителен
            TokenExpiredError: Если токен истек
            UserNotFoundError: Если пользователь не найден
        """
        self.logger.info("Запрос на установку нового пароля")

        try:
            # Проверяем и декодируем токен
            payload = TokenManager.verify_token(reset_data.token)

            user_id = TokenManager.validate_password_reset_token(payload)

            # Проверяем существование пользователя
            user = await self.data_manager.get_item_by_field("id", user_id)
            if not user:
                self.logger.warning(
                    "Пользователь не найден", extra={"user_id": str(user_id)}
                )
                raise UserNotFoundError(field="id", value=user_id)

            # Хешируем новый пароль
            hashed_password = PasswordHasher.hash_password(reset_data.new_password)

            # Обновляем пароль в БД
            await self.data_manager.update_items(
                user_id, {"hashed_password": hashed_password}
            )

            self.logger.info("Пароль успешно изменен", extra={"user_id": str(user_id)})

            confirm_data = PasswordResetConfirmDataSchema(
                password_changed_at=datetime.now(timezone.utc)
            )

            return PasswordResetConfirmResponseSchema(
                message="Пароль успешно изменен", data=confirm_data
            )

        except (TokenExpiredError, TokenInvalidError) as e:
            self.logger.error("Ошибка проверки токена сброса пароля: %s", e)
            raise
        except Exception as e:
            self.logger.error("Ошибка при сбросе пароля: %s", e)
            raise
