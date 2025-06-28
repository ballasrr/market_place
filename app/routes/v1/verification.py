"""
Роутер для верификации email пользователей.

Модуль содержит маршруты для подтверждения email адресов,
повторной отправки писем верификации и проверки статуса.

Routes:
    GET /register/verify-email/{token} - Подтверждение email по токену
    POST /verification/resend - Повторная отправка письма верификации
    GET /verification/status/{email} - Проверка статуса верификации

Classes:
    VerificationRouter: Класс для настройки маршрутов верификации
"""

from typing import Optional

from fastapi import Depends, Query, Response
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_redis_client
from app.routes.base import BaseRouter
from app.schemas import (ResendVerificationRequestSchema,
                         ResendVerificationResponseSchema,
                         TokenExpiredResponseSchema,
                         TokenInvalidResponseSchema,
                         UserNotFoundResponseSchema,
                         VerificationResponseSchema,
                         VerificationStatusResponseSchema)
from app.services.v1.registration.service import RegisterService


class VerificationRouter(BaseRouter):
    """
    Класс для настройки маршрутов верификации email.

    Предоставляет маршруты для:
    - Подтверждения email адресов по токену
    - Повторной отправки писем верификации
    - Проверки статуса верификации email

    Attributes:
        router (APIRouter): FastAPI роутер с настроенными маршрутами
    """

    def __init__(self):
        """
        Инициализирует роутер верификации.
        """
        super().__init__(prefix="verification", tags=["Verification"])

    def configure(self):
        """
        Настраивает все маршруты верификации.

        Определяет endpoints для повторной отправки писем верификации,
        проверки статуса и подтверждения email.
        """

        @self.router.get(
            path="/verify-email/{token}",
            response_model=VerificationResponseSchema,
            summary="Подтверждение email адреса",
            # description="Подтверждает email адрес пользователя по токену из письма",
            responses={
                200: {
                    "model": VerificationResponseSchema,
                    "description": "Email успешно подтвержден",
                },
                400: {
                    "model": TokenInvalidResponseSchema,
                    "description": "Недействительный токен верификации",
                },
                419: {
                    "model": TokenExpiredResponseSchema,
                    "description": "Срок действия токена истек",
                },
                404: {
                    "model": UserNotFoundResponseSchema,
                    "description": "Пользователь не найден",
                },
            },
        )
        async def verify_email(
            token: str,
            response: Response,
            use_cookies: bool = Query(
                False, description="Обновить куки с полными токенами"
            ),
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> VerificationResponseSchema:
            """
            ## ✅ Подтверждение email адреса

            Подтверждает email пользователя по токену из письма и выдает полные токены доступа.

            ### Параметры:
            * **token**: Токен верификации из письма
            * **use_cookies**: Обновить куки с полными токенами

            ### Returns:
            * Результат верификации с полными токенами доступа

            ### Процесс верификации:
            1. Валидация токена верификации
            2. Обновление статуса is_verified=true
            3. Выдача полных токенов доступа
            4. Отправка письма об успешной регистрации
            5. Опциональное обновление куков
            """
            return await RegisterService(session, redis).verify_email(
                token, response, use_cookies
            )

        @self.router.post(
            path="/resend",
            response_model=ResendVerificationResponseSchema,
            summary="Повторная отправка письма верификации",
            # description="Отправляет новое письмо для подтверждения email адреса",
            responses={
                200: {
                    "model": ResendVerificationResponseSchema,
                    "description": "Письмо верификации отправлено",
                },
                404: {
                    "model": UserNotFoundResponseSchema,
                    "description": "Пользователь не найден",
                },
            },
        )
        async def resend_verification_email(
            request: ResendVerificationRequestSchema,
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> ResendVerificationResponseSchema:
            """
            ## 📧 Повторная отправка письма для подтверждения email

            Отправляет новое письмо для подтверждения email адреса зарегистрированного пользователя.
            Используется когда пользователь не получил первоначальное письмо или оно истекло.

            ### Параметры:
            * **email**: Email адрес пользователя для повторной отправки

            ### Returns:
            * Статус отправки письма
            """
            return await RegisterService(session, redis).resend_verification_email(
                request.email
            )

        @self.router.get(
            path="/status/{email}",
            response_model=VerificationStatusResponseSchema,
            summary="Проверка статуса верификации",
            # description="Проверяет, подтвержден ли email адрес пользователя",
            responses={
                200: {
                    "model": VerificationStatusResponseSchema,
                    "description": "Статус верификации получен",
                },
                404: {
                    "model": UserNotFoundResponseSchema,
                    "description": "Пользователь не найден",
                },
            },
        )
        async def check_verification_status(
            email: str,
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
        ) -> VerificationStatusResponseSchema:
            """
            ## ✅ Проверка статуса верификации

            Проверяет, подтвержден ли email адрес пользователя в системе.
            Полезно для проверки необходимости повторной отправки письма.

            ### Параметры:
            * **email**: Email адрес для проверки статуса

            ### Returns:
            * **email**: Проверяемый email адрес
            * **is_verified**: Статус верификации (true/false)

            ### Использование:
            * Проверка перед повторной отправкой письма
            * Отображение статуса в интерфейсе пользователя
            * Валидация для операций, требующих подтвержденный email
            """
            return await RegisterService(session, redis).check_verification_status(
                email
            )
