"""
Роутер для управления пользователями.

Модуль содержит маршруты для получения списка пользователей...

Routes:
    GET /users - Получение списка пользователей с пагинацией и фильтрацией

Classes:
    UserRouter: Класс для настройки маршрутов пользователей
"""

from typing import Optional

from fastapi import Depends, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_redis_client
from app.core.security.auth import get_current_user
from app.models import UserRole
from app.routes.base import BaseRouter
from app.schemas import (
    CurrentUserSchema,
    ForbiddenResponseSchema,
    Page,
    PaginationParams,
    TokenMissingResponseSchema,
    UserListResponseSchema,
    UserSortFields,
)
from app.services.v1.users.service import UserService


class UserRouter(BaseRouter):
    """
    Класс для настройки маршрутов пользователей.

    Этот класс предоставляет маршруты для управления пользователями,
    такие как получение списка пользователей, получение статуса пользователя,
    изменение статуса пользователя, назначение роли пользователю,
    обновление роли пользователя и удаление пользователя.
    """

    def __init__(self):
        """
        Инициализирует роутер пользователей.
        """
        super().__init__(prefix="users", tags=["Users"])

    def configure(self):
        """
        Настраивает все маршруты пользователей.

        Определяет endpoints для получения списка пользователей...
        """

        @self.router.get(
            path="",
            response_model=UserListResponseSchema,
            responses={
                401: {
                    "model": TokenMissingResponseSchema,
                    "description": "Токен отсутствует",
                },
                403: {
                    "model": ForbiddenResponseSchema,
                    "description": "Недостаточно прав для выполнения операции",
                },
            },
        )
        async def get_users(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            sort_by: Optional[str] = Query(
                UserSortFields.get_default().field,
                description=(
                    "Поле для сортировки пользователей. "
                    f"Доступные значения: {', '.join(UserSortFields.get_field_values())}. "
                    f"По умолчанию: {UserSortFields.get_default().field} "
                    f"({UserSortFields.get_default().description})."
                ),
                enum=UserSortFields.get_field_values(),
            ),
            sort_desc: bool = Query(True, description="Сортировка по убыванию"),
            role: Optional[UserRole] = Query(
                None, description="Фильтрация по роли пользователя"
            ),
            search: Optional[str] = Query(
                None, description="Поиск по данным пользователя"
            ),
            session: AsyncSession = Depends(get_db_session),
            redis: Optional[Redis] = Depends(get_redis_client),
            current_user: CurrentUserSchema = Depends(get_current_user),
        ) -> UserListResponseSchema:
            """
            ## 📋 Получение списка пользователей

            Возвращает список пользователей с пагинацией, фильтрацией и поиском

            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **sort_by**: Поле для сортировки
            * **sort_desc**: Сортировка по убыванию
            * **role**: Роль пользователя для фильтрации
            * **search**: Строка поиска по данным пользователя

            ### Returns:
            * Страница с пользователями
            """
            pagination = PaginationParams(
                skip=skip, limit=limit, sort_by=sort_by, sort_desc=sort_desc
            )

            users, total = await UserService(session, redis).get_users(
                pagination=pagination,
                role=role,
                search=search,
                current_user=current_user,
            )
            page = Page(
                items=users, total=total, page=pagination.page, size=pagination.limit
            )
            return UserListResponseSchema(data=page)
