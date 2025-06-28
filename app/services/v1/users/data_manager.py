"""
Базовый менеджер данных для работы с пользователями.
"""

from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel, UserRole
from app.schemas import PaginationParams, UserSchema
from app.services.v1.base import BaseEntityManager


class UserDataManager(BaseEntityManager[UserSchema]):
    """
    Базовый менеджер для работы с пользователями.

    Содержит общие методы для работы с пользователями,
    которые используются в разных сервисах.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=UserSchema, model=UserModel)

    async def get_user_by_identifier(self, identifier: str) -> Optional[UserModel]:
        """
        Находит пользователя по email, username или телефону.

        Args:
            identifier: Email, username или телефон

        Returns:
            UserModel | None: Найденная модель или None
        """
        statement = select(UserModel).where(
            or_(
                UserModel.email == identifier,
                UserModel.username == identifier,
                UserModel.phone == identifier,
            )
        )
        user = await self.get_one(statement)

        if user:
            self.logger.info(
                "Пользователь найден",
                extra={"identifier": identifier, "user_id": user.id},
            )
        else:
            self.logger.info("Пользователь не найден", extra={"identifier": identifier})

        return user

    async def get_users(
        self,
        pagination: PaginationParams,
        role: UserRole = None,
        search: str = None,
    ) -> tuple[List[UserSchema], int]:
        """
        Получает список пользователей с возможностью пагинации, поиска и фильтрации.

        Args:
            pagination (PaginationParams): Параметры пагинации
            role (UserRole): Фильтрация по роли пользователя
            search (str): Поиск по тексту пользователя

        Returns:
            tuple[List[UserSchema], int]: Список пользователей и их общее количество
        """
        statement = select(self.model).distinct()

        # Поиск по тексту (имя пользователя или email)
        if search:
            statement = statement.filter(
                or_(
                    self.model.username.ilike(f"%{search}%"),
                    self.model.email.ilike(f"%{search}%"),
                )
            )

        # Фильтр по роли пользователя
        if role:
            statement = statement.filter(self.model.role == role)

        return await self.get_paginated_items(statement, pagination)
