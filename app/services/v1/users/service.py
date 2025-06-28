"""
Модуль для работы с пользователями.

Этот модуль содержит основные классы для управления пользователями в системе:
- UserService: Сервисный слой для бизнес-логики работы с пользователями
- UserDataManager: Слой доступа к данным для работы с БД

Основные операции:
- Создание пользователей
- Получение пользователей по email
- Обновление данных пользователей
- Удаление пользователей

Пример использования:
    service = UserService(session)
    user = await service.create_user(user_data)
    user_by_email = await service.get_user_by_email("test@test.com")
"""

from typing import List

from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.core.integrations.cache.auth import AuthRedisDataManager
from app.models import UserRole
from app.schemas import CurrentUserSchema, PaginationParams, UserSchema
from app.services.v1.base import BaseService
from app.services.v1.users.data_manager import UserDataManager


class UserService(BaseService):
    """
    Сервис для управления пользователями.

    Предоставляет высокоуровневые методы для работы с пользователями,
    инкапсулируя бизнес-логику и взаимодействие с базой данных.

    Attributes:
        session (AsyncSession): Асинхронная сессия для работы с БД

    Methods:
        get_users Получает список пользователей с возможностью пагинации, поиска и фильтрации.
    """

    def __init__(self, session: AsyncSession, redis: Redis = None):
        """
        Инициализирует сервис аутентификации.

        Args:
            session: Асинхронная сессия базы данных
        """
        super().__init__(session)
        self.data_manager = UserDataManager(session)
        self.redis_data_manager = AuthRedisDataManager(redis)

    async def get_users(
        self,
        pagination: PaginationParams,
        role: UserRole = None,
        search: str = None,
        current_user: CurrentUserSchema = None,
    ) -> tuple[List[UserSchema], int]:
        """
        Получает список пользователей с возможностью пагинации, поиска и фильтрации.

        Args:
            pagination (PaginationParams): Параметры пагинации
            role (UserRole): Фильтрация по роли пользователя
            search (str): Поиск по тексту пользователя
            current_user (CurrentUserSchema): Текущий авторизованный пользователь

        Returns:
            tuple[List[UserSchema], int]: Список пользователей и общее количество пользователей.

        Raises:
            ForbiddenError: Если у пользователя недостаточно прав для просмотра списка пользователей
        """
        allowed_roles = [UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER]
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                detail="Только администраторы и модераторы могут просматривать список пользователей",
                required_role=f"{UserRole.ADMIN.value} или {UserRole.MODERATOR.value}",
            )

        if current_user.role == UserRole.USER:
            if role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
                raise ForbiddenError(
                    detail="У вас недостаточно прав для просмотра администраторов",
                    required_role=UserRole.ADMIN.value,
                )

        users, total = await self.data_manager.get_users(
            pagination=pagination,
            role=role,
            search=search,
        )

        for user in users:
            user.is_online = await self.redis_data_manager.get_online_status(user.id)

        return users, total
