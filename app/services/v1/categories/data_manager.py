from typing import List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category
from app.schemas import (
    CategoryCreateSchema,
    CategoryDataSchema,
    CategoryUpdateSchema,
    PaginationParams,
)
from app.services.v1.base import BaseEntityManager


class CategoryDataManager(BaseEntityManager[CategoryDataSchema]):
    """
    Менеджер данных для работы с категориями товаров.
    Реализует низкоуровневые операции для работы с таблицами категорий в БД.
    Обрабатывает исключения БД и преобразует их в доменные исключения.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
        schema (Type[CategorySchema]): Схема сериализации данных
        model (Type[CategoryModel]): Модель категории товаров

    Methods:
        add_category: Добавление новой категории в БД
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=CategoryDataSchema, model=Category)

    async def add_category(self, data: CategoryCreateSchema) -> Category:
        category_model = Category(
            title=data.title, description=data.description, parent_id=data.parent_id
        )
        return await self.add_one(category_model)

    async def update_category(
        self, category: Category, data: CategoryUpdateSchema
    ) -> Category:
        category_data_dict = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in category_data_dict.items():
            setattr(category, key, value)
        return await self.update_one(category)

    async def update_image(self, category: Category, image_url: str) -> None:
        try:
            await self.update_items(category.id, {"image": image_url})
        except (ValueError, SQLAlchemyError):
            self.logger.error(
                "Не удалось обновить изображение для категории %s", category.id
            )
            raise RuntimeError(
                f"Не удалось обновить изображение для категории {category.id}"
            )

    async def get_all_categories(
        self,
        pagination: PaginationParams,
        search: str = None,
    ) -> List[Category]:
        statement = (
            select(Category)
            .options(
                selectinload(Category.children),
                selectinload(Category.parent),
            )
            .distinct()
        )
        if search:
            statement = statement.filter(self.model.title.ilike(f"%{search}%"))
        return await self.get_paginated_items(statement, pagination)

    async def get_category_by_id(self, category_id: int) -> Category:
        statement = (
            select(Category)
            .where(Category.id == category_id)
            .options(
                selectinload(Category.children),
                selectinload(Category.parent),
            )
        )
        return await self.get_one(statement)
