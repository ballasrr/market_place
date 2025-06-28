"""
Роутер для аутентификации пользователей.

Модуль содержит маршруты для аутентификации, включая вход в систему,
обновление токенов, выход и восстановление пароля. Обеспечивает
безопасную аутентификацию с использованием JWT токенов.

Routes:
    POST /auth - Аутентификация пользователя
    POST /auth/refresh - Обновление токена доступа
    POST /auth/logout - Выход из системы
    POST /auth/forgot-password - Запрос восстановления пароля
    POST /auth/reset-password - Подтверждение сброса пароля

Classes:
    AuthRouter: Класс для настройки маршрутов аутентификации
"""

from typing import Optional

from fastapi import Cookie, Depends, Header, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_redis_client
from app.core.exceptions import TokenMissingError
from app.routes.base import BaseRouter
from app.schemas import (ForgotPasswordSchema,
                         InvalidCredentialsResponseSchema,
                         LogoutResponseSchema,
                         PasswordResetConfirmResponseSchema,
                         PasswordResetConfirmSchema,
                         PasswordResetResponseSchema,
                         RateLimitExceededResponseSchema,
                         TokenExpiredResponseSchema,
                         TokenInvalidResponseSchema,
                         TokenMissingResponseSchema, TokenResponseSchema,
                         UserInactiveResponseSchema,
                         WeakPasswordResponseSchema)
from app.services.v1.auth.service import AuthService


class AuthRouter(BaseRouter):
    """
    Класс для настройки маршрутов аутентификации.

    Предоставляет маршруты для аутентификации пользователей, включая:
    - Вход в систему с получением JWT токенов
    - Обновление токенов доступа
    - Выход из системы
    - Восстановление пароля

    Все маршруты включают обработку ошибок и соответствующие HTTP коды ответов.

    Attributes:
        router (APIRouter): FastAPI роутер с настроенными маршрутами
    """

    def __init__(self):
        """
        Инициализирует роутер аутентификации.
        """
        super().__init__(prefix="auth", tags=["Authentication"])

    def configure(self):
        """
        Настраивает все маршруты аутентификации.

        Определяет endpoints для входа, обновления токенов, выхода
        и восстановления пароля с соответствующими схемами ответов.
        """

        @self.router.post(
            path="",
            response_model=TokenResponseSchema,
            summary="Аутентификация пользователя",
            # description="Аутентифицирует пользователя и возвращает JWT токены",
            responses={
                200: {
                    "model": TokenResponseSchema,
                    "description": "Успешная аутентификация",
                },
                401: {
                    "model": InvalidCredentialsResponseSchema,
                    "description": "Неверные учетные данные",
                },
                403: {
                    "model": UserInactiveResponseSchema,
                    "description": "Аккаунт пользователя деактивирован",
                },
                429: {
                    "model": RateLimitExceededResponseSchema,
                    "description": "Превышен лимит запросов",
                },
            },
        )
        async def authenticate(
            response: Response,
            form_data: OAuth2PasswordRequestForm = Depends(),
            use_cookies: bool = Query(
                False, description="Использовать куки для хранения токенов"
            ),
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> TokenResponseSchema:
            """
            ## 🔐 Аутентификация пользователя с опциональным использованием куков

            Аутентифицирует пользователя по имени, email или телефону и возвращает JWT токены.

            ### Для аутентификации используйте один из вариантов:
            * **Email-адрес**: user@example.com
            * **Имя пользователя**: john_doe
            * **Телефон**: +7 (XXX) XXX-XX-XX

            ### Параметры:
            * **username**: Email, имя пользователя или телефон
            * **password**: Пароль пользователя
            * **use_cookies**: Булево значение, указывающее, использовать ли куки для хранения токенов (по умолчанию False)

            ### Returns:
            * **success**: Булево значение успешности аутентификации
            * **message**: Сообщение об успешной аутентификации
            * **access_token**: JWT токен доступа (срок действия: 15 минут)
            * **refresh_token**: Refresh токен для обновления (срок действия: 7 дней)
            * **token_type**: Тип токена (Bearer)
            * **expires_in**: Время жизни access токена в секундах
            """
            return await AuthService(session, redis).authenticate(
                form_data, response, use_cookies
            )

        @self.router.post(
            path="/refresh",
            response_model=TokenResponseSchema,
            summary="Обновление токена доступа",
            # description="Получение нового access токена с помощью refresh токена",
            responses={
                200: {
                    "model": TokenResponseSchema,
                    "description": "Токен успешно обновлен",
                },
                401: {
                    "model": TokenMissingResponseSchema,
                    "description": "Refresh токен отсутствует",
                },
                419: {
                    "model": TokenExpiredResponseSchema,
                    "description": "Refresh токен просрочен",
                },
                422: {
                    "model": TokenInvalidResponseSchema,
                    "description": "Невалидный refresh токен",
                },
                429: {
                    "model": RateLimitExceededResponseSchema,
                    "description": "Превышен лимит запросов",
                },
            },
        )
        async def refresh_token(
            response: Response,
            use_cookies: bool = Query(
                False, description="Использовать куки для токенов"
            ),
            refresh_token_header: str = Header(None, alias="refresh-token"),
            refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> TokenResponseSchema:
            """
            ## 🔄 Обновление токена доступа

            Получение нового access токена с помощью refresh токена.
            Используется когда access токен истек, но refresh токен еще действителен.

            ### Заголовки:
            * **refresh_token_header**: Refresh токен, полученный при аутентификации
            * **refresh_token_cookie**: Refresh токен из куки (если используется куки)
            * **use_cookies**: Булево значение, указывающее, использовать ли куки для хранения токенов (по умолчанию False)

            ### Returns:
            * **success**: Булево значение успешности обновления токена
            * **message**: Сообщение об успешном обновлении токена
            * **data**: Данные обновленного токена
                * **access_token**: Новый JWT токен доступа
                * **refresh_token**: Новый refresh токен (ротация токенов)
                * **token_type**: Тип токена (Bearer)
                * **expires_in**: Время жизни нового access токена в секундах

            ### Безопасность:
            * Refresh токены имеют ограниченный срок действия
            * При каждом обновлении выдается новый refresh токен
            * Старый refresh токен становится недействительным
            """
            # Приоритет: заголовок -> кука
            refresh_token = refresh_token_header or refresh_token_cookie

            if not refresh_token:
                raise TokenMissingError()

            return await AuthService(session, redis).refresh_token(
                refresh_token, response, use_cookies
            )

        @self.router.post(
            path="/logout",
            response_model=LogoutResponseSchema,
            summary="Выход из системы",
            # description="Завершение сессии пользователя и аннулирование токенов",
            responses={
                200: {
                    "model": LogoutResponseSchema,
                    "description": "Успешный выход из системы",
                },
                401: {
                    "model": TokenMissingResponseSchema,
                    "description": "Токен отсутствует",
                },
                422: {
                    "model": TokenInvalidResponseSchema,
                    "description": "Невалидный токен",
                },
            },
        )
        async def logout(
            response: Response,
            clear_cookies: bool = Query(False, description="Очистить куки при выходе"),
            authorization: str = Header(None, description="Токен доступа"),
            access_token_cookie: str = Cookie(None, alias="access_token"),
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> LogoutResponseSchema:
            """
            ## 🚪 Выход из системы

            Завершает сессию пользователя и добавляет токены в черный список.
            После выхода все токены пользователя становятся недействительными.

            ### Заголовки:
            * **authorization**: Bearer токен для идентификации сессии

            ### Returns:
            * **success**: Булево значение успешности выхода
            * **message**: Сообщение о успешном выходе
            * **logged_out_at**: Время выхода из системы

            ### Безопасность:
            * Токены добавляются в черный список
            * Все активные сессии пользователя завершаются
            * Требуется повторная аутентификация для доступа
            """
            if not authorization and access_token_cookie:
                authorization = f"Bearer {access_token_cookie}"

            return await AuthService(session, redis).logout(
                authorization, response, clear_cookies
            )

        @self.router.post(
            path="/forgot-password",
            response_model=PasswordResetResponseSchema,
            summary="Запрос восстановления пароля",
            # description="Отправка ссылки для сброса пароля на email",
            responses={
                200: {
                    "model": PasswordResetResponseSchema,
                    "description": "Ссылка для сброса пароля отправлена",
                },
                404: {"description": "Пользователь с указанным email не найден"},
                429: {
                    "model": RateLimitExceededResponseSchema,
                    "description": "Превышен лимит запросов на восстановление",
                },
            },
        )
        async def forgot_password(
            request: ForgotPasswordSchema,
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> PasswordResetResponseSchema:
            """
            ## 📧 Запрос восстановления пароля

            Отправляет ссылку для сброса пароля на указанный email адрес.
            Ссылка действительна в течение ограниченного времени.

            ### Параметры:
            * **email**: Email адрес для отправки ссылки восстановления

            ### Returns:
            * **success**: Булево значение успешности отправки ссылки
            * **message**: Сообщение о отправке ссылки
            * **email**: Email, на который отправлена ссылка
            * **expires_in**: Время действия ссылки в секундах

            ### Безопасность:
            * Ограничение на количество запросов с одного IP
            * Ссылки имеют ограниченный срок действия
            * Одноразовые токены для сброса пароля
            """
            return await AuthService(session, redis).send_password_reset_email(
                request.email
            )

        @self.router.post(
            path="/reset-password",
            response_model=PasswordResetConfirmResponseSchema,
            summary="Подтверждение сброса пароля",
            # description="Установка нового пароля по токену восстановления",
            responses={
                200: {
                    "model": PasswordResetConfirmResponseSchema,
                    "description": "Пароль успешно изменен",
                },
                400: {
                    "model": WeakPasswordResponseSchema,
                    "description": "Пароль не соответствует требованиям безопасности",
                },
                419: {
                    "model": TokenExpiredResponseSchema,
                    "description": "Токен восстановления просрочен",
                },
                422: {
                    "model": TokenInvalidResponseSchema,
                    "description": "Невалидный токен восстановления",
                },
            },
        )
        async def reset_password(
            reset_data: PasswordResetConfirmSchema,
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> PasswordResetConfirmResponseSchema:
            """
            ## 🔑 Подтверждение сброса пароля

            Устанавливает новый пароль пользователя по токену восстановления.
            Токен получается из ссылки, отправленной на email.

            ### Параметры:
            * **token**: Токен восстановления из email ссылки
            * **new_password**: Новый пароль пользователя
            * **confirm_password**: Подтверждение нового пароля

            ### Returns:
            * **success**: Булево значение успешности изменения пароля
            * **message**: Сообщение о успешном изменении пароля
            * **password_changed_at**: Время изменения пароля

            ### Требования к паролю:
            * Минимум 8 символов
            * Содержит буквы и цифры
            * Содержит специальные символы
            * Не совпадает с предыдущими паролями

            ### Безопасность:
            * Токены одноразовые и имеют ограниченный срок действия
            * Пароли хешируются с использованием bcrypt
            * Все предыдущие сессии пользователя завершаются
            * Токен становится недействительным после использования
            """
            return await AuthService(session, redis).reset_password(reset_data)
