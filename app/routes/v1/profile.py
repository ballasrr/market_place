from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.core.security.auth import get_current_user
from app.routes.base import BaseRouter
from app.schemas import (CurrentUserSchema, PasswordFormSchema,
                         PasswordUpdateResponseSchema, ProfileResponseSchema,
                         ProfileUpdateSchema)
from app.schemas.v1.auth.exception import TokenMissingResponseSchema
from app.schemas.v1.profile.exception import (
    InvalidCurrentPasswordResponseSchema, ProfileNotFoundResponseSchema,
    UserNotFoundResponseSchema)
from app.services.v1.profile.service import ProfileService


class ProfileRouter(BaseRouter):
    def __init__(self):
        super().__init__(prefix="profile", tags=["Profile"])

    def configure(self):
        @self.router.get(path="", response_model=ProfileResponseSchema)
        async def get_profile(
            session: AsyncSession = Depends(get_db_session),
            current_user: CurrentUserSchema = Depends(get_current_user),
        ) -> ProfileResponseSchema:
            """
            ## 👤 Получение профиля пользователя

            Возвращает данные профиля текущего авторизованного пользователя

            ### Returns:
            * **ProfileResponseSchema**: Полная информация о профиле пользователя
            """
            return await ProfileService(session).get_profile(current_user)

        @self.router.put(
            path="",
            response_model=ProfileResponseSchema,
            responses={
                401: {
                    "model": TokenMissingResponseSchema,
                    "description": "Токен отсутствует",
                },
                404: {
                    "model": ProfileNotFoundResponseSchema,
                    "description": "Профиль не найден",
                },
            },
        )
        async def update_profile(
            profile_data: ProfileUpdateSchema,
            session: AsyncSession = Depends(get_db_session),
            current_user: CurrentUserSchema = Depends(get_current_user),
        ) -> ProfileResponseSchema:
            """
            ## ✏️ Обновление профиля пользователя

            Изменяет основные данные профиля текущего пользователя

            ### Args:
            * **username**: Имя пользователя (опционально)
            * **email**: Email пользователя (опционально)
            * **phone**: Телефон пользователя в формате +7 (XXX) XXX-XX-XX (опционально)

            ### Returns:
            * **ProfileResponseSchema**: Обновленная информация о профиле пользователя
            """
            return await ProfileService(session).update_profile(
                current_user, profile_data
            )

        @self.router.put(
            path="/password",
            response_model=PasswordUpdateResponseSchema,
            responses={
                400: {
                    "model": InvalidCurrentPasswordResponseSchema,
                    "description": "Текущий пароль неверен",
                },
                401: {
                    "model": TokenMissingResponseSchema,
                    "description": "Токен отсутствует",
                },
                404: {
                    "model": UserNotFoundResponseSchema,
                    "description": "Пользователь не найден",
                },
            },
        )
        async def update_password(
            password_data: PasswordFormSchema,
            session: AsyncSession = Depends(get_db_session),
            current_user: CurrentUserSchema = Depends(get_current_user),
        ) -> PasswordUpdateResponseSchema:
            """
            ## 🔄 Обновление пароля пользователя

            Изменяет пароль текущего пользователя

            ### Args:
            * **old_password**: Текущий пароль
            * **new_password**: Новый пароль
            * **confirm_password**: Подтверждение нового пароля

            ### Returns:
            * Статус операции изменения пароля
            """
            return await ProfileService(session).update_password(
                current_user, password_data
            )
