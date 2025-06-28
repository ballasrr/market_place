"""
Сервис для работы с профилем пользователя.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProfileNotFoundError, UserNotFoundError
from app.core.security.password import PasswordHasher
from app.schemas import (CurrentUserSchema, PasswordFormSchema,
                         PasswordUpdateResponseSchema, ProfileResponseSchema,
                         ProfileUpdateSchema)
from app.services.v1.base import BaseService

from .data_manager import ProfileDataManager


class ProfileService(BaseService):
    """
    Сервис для работы с профилем пользователя.

    Attributes:
        session: Асинхронная сессия для работы с базой данных."

    """

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        super().__init__(db_session)
        self.data_manager = ProfileDataManager(db_session)

    async def get_profile(self, user: CurrentUserSchema) -> ProfileResponseSchema:
        """
        Получает профиль пользователя по ID пользователя.

        Args:
            user: (CurrentUserSchema) Объект пользователя

        Returns:
            ProfileResponseSchema: Профиль пользователя.
        """

        profile_data = await self.data_manager.get_item(user.id)

        if profile_data is None:
            raise ProfileNotFoundError()

        return ProfileResponseSchema(data=profile_data)

    async def update_profile(
        self, user: CurrentUserSchema, profile_data: ProfileUpdateSchema
    ) -> ProfileResponseSchema:
        """
        Обновляет профиль пользователя.

        Args:
            user: Объект пользователя
            profile_data (ProfileUpdateSchema): Данные профиля пользователя.

        Returns:
            ProfileResponseSchema: Обновленный профиль пользователя.
        """
        update_data = profile_data.model_dump(exclude_unset=True)

        updated_profile = await self.data_manager.update_items(user.id, update_data)

        return ProfileResponseSchema(
            message="Данные профиля успешно обновлены", data=updated_profile
        )

    async def update_password(
        self, current_user: CurrentUserSchema, password_data: PasswordFormSchema
    ) -> PasswordUpdateResponseSchema:
        """
        Обновляет пароль пользователя.

        Args:
            current_user: (CurrentUserSchema) Объект пользователя
            password_data (PasswordFormSchema): Данные нового пароля пользователя.

        Returns:
            PasswordUpdateResponseSchema: Объект с полями:
            - success (bool): Статус успешного обновления пароля
            - message (str): Сообщение о результате операции

        Raises:
            InvalidCurrentPasswordError: Если текущий пароль неверен
            UserNotFoundError: Если пользователь не найден
        """
        user_model = await self.data_manager.get_model_by_field("id", current_user.id)
        if not user_model:
            raise UserNotFoundError(
                field="id",
                value=current_user.id,
            )

        # Старый (существующий) пароль вводить не нужно

        # if not PasswordHasher.verify(
        #     user_model.hashed_password, password_data.old_password
        # ):
        #     raise InvalidCurrentPasswordError()

        new_hashed_password = PasswordHasher.hash_password(password_data.new_password)

        await self.data_manager.update_items(
            current_user.id, {"hashed_password": new_hashed_password}
        )

        return PasswordUpdateResponseSchema()
