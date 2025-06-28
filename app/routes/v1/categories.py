from typing import Optional

from fastapi import Depends, File, Form, UploadFile
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.dependencies import get_db_session
from app.core.integrations.storage import CategoryS3DataManager, get_category_s3_manager
from app.core.security.auth import get_current_user
from app.models import UserModel
from app.routes.base import BaseRouter
from app.schemas import (
    CategoryCreateSchema,
    CategoryListResponseSchema,
    CategoryResponseSchema,
    CategoryUpdateSchema,
    Page,
    PaginationParams,
)
from app.services.v1.categories.service import CategoryService


class CategoryRouter(BaseRouter):
    def __init__(self):
        super().__init__(prefix="categories", tags=["Categories"])

    def configure(self):
        @self.router.post(
            path="",
            response_model=CategoryResponseSchema,
            status_code=status.HTTP_201_CREATED,
            summary="Создание новой категории",
        )
        async def create_category(
            new_category: CategoryCreateSchema,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> CategoryResponseSchema:
            return await CategoryService(session).create_category(user, new_category)

        @self.router.get(
            path="",
            response_model=CategoryListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение всех категорий",
        )
        async def get_all_categories(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            search: Optional[str] = Query(
                None, description="Поиск по данным категории"
            ),
            session: AsyncSession = Depends(get_db_session),
        ) -> CategoryListResponseSchema:
            """
            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **search**: Строка поиска по данным категории
            """
            pagination = PaginationParams(skip=skip, limit=limit)
            categories, total = await CategoryService(session).get_all_categories(
                pagination=pagination,
                search=search,
            )
            page = Page(
                items=categories,
                total=total,
                page=pagination.page,
                size=pagination.limit,
            )
            return CategoryListResponseSchema(data=page)

        @self.router.patch(
            path="/{category_id}",
            response_model=CategoryResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Обновление категории",
        )
        async def update_category(
            category_id: int,
            title: Optional[str] = Form(None),
            description: Optional[str] = Form(None),
            parent_id: Optional[int] = Form(None),
            image: Optional[UploadFile] = File(None),
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
            s3_data_manager: CategoryS3DataManager = Depends(get_category_s3_manager),
        ) -> CategoryResponseSchema:
            category_data = CategoryUpdateSchema(
                title=title, description=description, parent_id=parent_id
            )
            return await CategoryService(session, s3_data_manager).update_category(
                user, category_id, category_data, image
            )

        @self.router.get(
            path="/{category_id}",
            response_model=CategoryResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение категории по ID",
        )
        async def get_category_by_id(
            category_id: int,
            session: AsyncSession = Depends(get_db_session),
        ) -> CategoryResponseSchema:
            return await CategoryService(session).get_category_by_id(category_id)

        @self.router.delete(
            path="/{category_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удаление категории по ID",
        )
        async def delete_category(
            category_id: int,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> None:
            await CategoryService(session).delete_category(user, category_id)
