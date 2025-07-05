from typing import Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.dependencies import get_db_session
from app.core.security.auth import get_current_user
from app.models import UserModel
from app.routes.base import BaseRouter
from app.schemas import (
    PaginationParams,
    FavoriteListResponseSchema,
    FavoriteResponseSchema,
)
from app.services.v1.favorites.service import FavoriteService


class FavoriteRouter(BaseRouter):
    def __init__(self):
        super().__init__(prefix="/favorites", tags=["Favorites"])

    def configure(self):
        @self.router.post(
            path="/{product_id}",
            response_model=FavoriteResponseSchema,
            status_code=status.HTTP_201_CREATED,
            summary="Добавить товар в избранное",
            responses={
                404: {"description": "Товар не найден"},
                400: {"description": "Товар уже в избранном"},
                500: {"description": "Внутренняя ошибка сервера"},
            },
        )
        async def add_to_favorites(
            product_id: int,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> FavoriteResponseSchema:
            return await FavoriteService(session).add_to_favorites(user.id, product_id)

        @self.router.delete(
            path="/{product_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удалить товар из избранного",
            responses={
                404: {"description": "Товар не найден в избранном"},
                500: {"description": "Внутренняя ошибка сервера"},
            },
        )
        async def remove_from_favorites(
            product_id: int,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> None:
            await FavoriteService(session).remove_from_favorites(user.id, product_id)

        @self.router.get(
            path="",
            response_model=FavoriteListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получить список избранных товаров",
            responses={500: {"description": "Внутренняя ошибка сервера"}},
        )
        async def get_favorites(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> FavoriteListResponseSchema:
            pagination = PaginationParams(skip=skip, limit=limit)
            return await FavoriteService(session).get_user_favorites(user_id=user.id, pagination=pagination)
