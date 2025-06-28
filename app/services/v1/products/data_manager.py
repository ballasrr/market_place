from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.schemas import PaginationParams, ProductCreateSchema, ProductDataSchema
from app.services.v1.base import BaseEntityManager


class ProductDataManager(BaseEntityManager[ProductDataSchema]):
    """
    Менеджер данных для работы с продуктами.
    Реализует низкоуровневые операции для работы с таблицами продуктов в БД.
    Обрабатывает исключения БД и преобразует их в доменные исключения.
    Attributes:
        session (AsyncSession): Асинхронная сессия БД
        schema (Type[ProductDataSchema]): Схема сериализации данных
        model (Type[Product]): Модель продукта
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=ProductDataSchema, model=Product)

    async def get_by_id(self, product_id: int) -> Product:
        statement = select(Product).where(Product.id == product_id)
        return await self.get_one(statement)

    async def get_all_products(
        self,
        pagination: PaginationParams,
        search: str = None,
        category_id: Optional[int] = None,
    ) -> tuple[list[Product], int]:
        statement = select(Product)
        if search:
            statement = statement.filter(
                or_(
                    self.model.title.ilike(f"%{search}%"),
                    self.model.brand.ilike(f"%{search}%"),
                    self.model.material.ilike(f"%{search}%"),
                )
            )
        if category_id is not None:
            statement = statement.filter(self.model.category_id == category_id)
        return await self.get_paginated_items(statement, pagination)

    async def add_product(self, data: ProductCreateSchema) -> Product:
        product_model = Product(
            title=data.title,
            description=data.description,
            brand=data.brand,
            country=data.country,
            width=data.width,
            height=data.height,
            material=data.material,
            price=data.price,
            quantity=data.quantity,
            category_id=data.category_id,
        )
        return await self.add_one(product_model)

    async def update_product(
        self, product: Product, data: ProductCreateSchema
    ) -> Product:
        product_data_dict = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in product_data_dict.items():
            setattr(product, key, value)
        return await self.update_one(product)

    async def updata_product_images(
        self, product: Product, image_urls: List[str]
    ) -> None:
        try:
            await self.update_items(product.id, {"images": image_urls})
        except (ValueError, SQLAlchemyError):
            self.logger.error(
                "Не удалось обновить изображения для продукта %s", product.id
            )
            raise RuntimeError(
                f"Не удалось обновить изображения для продукта {product.id}"
            )

    async def get_best_selling_products(
        self,
        pagination: PaginationParams,
        limit: int = 10
    ) -> tuple[list[Product], int]:
        try:
            statement = (
                select(Product)
                .order_by(Product.sales_count.desc())
                .limit(limit)
            )
            return await self.get_paginated_items(statement, pagination)
        except SQLAlchemyError as e:
            self.logger.error("Ошибка при получении хитов продаж: %s", str(e))
            raise RuntimeError("Не удалось получить хиты продаж") from e

    async def get_products_with_biggest_discounts(
        self,
        pagination: PaginationParams,
        min_discount: float = 10.0,
        limit: int = 10
    ) -> tuple[list[Product], int]:
        try:
            statement = (
                select(Product)
                .where(Product.discount >= min_discount)
                .order_by(Product.discount.desc())
                .limit(limit)
            )
            return await self.get_paginated_items(statement, pagination)
        except SQLAlchemyError as e:
            self.logger.error("Ошибка при получении товаров со скидками: %s", str(e))
            raise RuntimeError("Не удалось получить товары со скидками") from e

    async def get_recently_added_products(
        self,
        pagination: PaginationParams,
        days_threshold: int = 30,
        limit: int = 10
    ) -> tuple[list[Product], int]:
        try:
            from datetime import datetime, timedelta
            threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

            statement = (
                select(Product)
                .where(Product.created_at >= threshold_date)
                .order_by(Product.created_at.desc())
                .limit(limit)
            )
            return await self.get_paginated_items(statement, pagination)
        except SQLAlchemyError as e:
            self.logger.error("Ошибка при получении новинок: %s", str(e))
            raise RuntimeError("Не удалось получить новинки") from e
