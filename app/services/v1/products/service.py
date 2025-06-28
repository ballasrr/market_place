from typing import List, Optional, Tuple

from botocore.exceptions import ClientError
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CategoryNotFoundError,
    ForbiddenError,
    ProductNotFoundError,
    StorageError,
)
from app.core.integrations.storage import ProductS3DataManager
from app.models import Product, UserModel
from app.schemas import PaginationParams, ProductCreateSchema, ProductResponseSchema
from app.services.v1.base import BaseService
from app.services.v1.categories.data_manager import CategoryDataManager
from app.services.v1.products.data_manager import ProductDataManager


class ProductService(BaseService):
    """
    Сервис для работы с продуктами.

    Attributes:
        session (AsyncSession): Асинхронная сессия для работы с базой данных.
        data_manager (ProductDataManager): Менеджер данных для операций с продуктами.
        category_data_manager (CategoryDataManager): Менеджер данных для операций с категориями.
        s3_data_manager (Optional[ProductS3DataManager]): Менеджер данных для работы с S3-хранилищем.
    Methods:
        get_all_products: Получает все продукты с возможностью пагинации и фильтра
        create_product: Создает новый продукт.
        get_product_by_id: Получает продукт по ID.
        delete_product: Удаляет продукт по ID.
        update_product: Обновляет существующий продукт.
        update_product_images: Обновляет изображения продукта.
    """

    def __init__(
        self,
        session: AsyncSession,
        s3_data_manager: Optional[ProductS3DataManager] = None,
    ):
        super().__init__(session)
        self.data_manager = ProductDataManager(session)
        self.category_data_manager = CategoryDataManager(session)
        self.s3_data_manager = s3_data_manager

    async def get_all_products(
        self,
        pagination: PaginationParams,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> Tuple[List[ProductResponseSchema], int]:
        products, total = await self.data_manager.get_all_products(
            pagination, search, category_id
        )
        return [
            ProductResponseSchema.model_validate(product) for product in products
        ], total

    async def create_product(
        self, user: UserModel, data: ProductCreateSchema
    ) -> Product:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для создания продукта",
                required_role="MODERATOR",
            )
        if data.category_id is not None:
            category = await self.category_data_manager.get_category_by_id(
                data.category_id
            )
            if not category:
                raise CategoryNotFoundError(
                    field="id", value=data.category_id, detail="Категория не найдена"
                )
        return await self.data_manager.add_product(data)

    async def get_product_by_id(self, product_id: int) -> ProductResponseSchema:
        product = await self.data_manager.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(
                field="id", value=product_id, detail="Продукт не найден"
            )
        return ProductResponseSchema.model_validate(product)

    async def delete_product(self, user: UserModel, product_id: int) -> None:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для удаления продукта",
                required_role="MODERATOR",
            )
        product = await self.data_manager.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(
                field="id", value=product_id, detail="Продукт не найден"
            )
        await self.data_manager.delete_item(product_id)

    async def update_product(
        self, user: UserModel, product_id: int, data: ProductCreateSchema
    ) -> ProductResponseSchema:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для обновления продукта",
                required_role="MODERATOR",
            )
        product = await self.data_manager.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(
                field="id", value=product_id, detail="Продукт не найден"
            )
        if data.category_id is not None:
            category = await self.category_data_manager.get_category_by_id(
                data.category_id
            )
            if not category:
                raise CategoryNotFoundError(
                    field="id", value=data.category_id, detail="Категория не найдена"
                )
        updated_product = await self.data_manager.update_product(product, data)
        return ProductResponseSchema.model_validate(updated_product)

    async def update_product_images(
        self,
        user: UserModel,
        product_id: int,
        files: List[UploadFile],
    ) -> ProductResponseSchema:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для обновления изображений продукта",
                required_role="MODERATOR",
            )
        product = await self.data_manager.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(
                field="id", value=product_id, detail="Продукт не найден"
            )

        old_image_urls = getattr(product, "images", None) or []
        self.logger.info("Текущие изображения: %s", old_image_urls)
        files_content = [await file.read() for file in files]

        try:
            image_urls = await self.s3_data_manager.process_product_images(
                old_image_urls=old_image_urls,
                files=files,
                files_content=files_content,
            )
            self.logger.info("Файлы загружены: %s", image_urls)
        except ClientError as e:
            self.logger.error("Ошибка S3 при загрузке изображения: %s", str(e))
            raise StorageError(detail=f"Ошибка хранилища: {str(e)}")
        except ValueError as e:
            self.logger.error("Ошибка валидации при загрузке изображения: %s", str(e))
            raise StorageError(detail=str(e))
        except Exception as e:
            self.logger.error("Неизвестная ошибка при загрузке изображения: %s", str(e))
            raise StorageError(detail=f"Ошибка при загрузке изображения: {str(e)}")

        await self.data_manager.updata_product_images(product, image_urls)
        updated_product = await self.data_manager.get_by_id(product_id)
        return ProductResponseSchema.model_validate(updated_product)

    async def get_best_sellers(
        self,
        pagination: PaginationParams,
        limit: int = 10
    ) -> Tuple[List[ProductResponseSchema], int]:
        """
        Получает список самых продаваемых продуктов (хиты продаж).

        Args:
            pagination: Параметры пагинации.
            limit: Максимальное количество продуктов (по умолчанию 10).

        Returns:
            Кортеж (список продуктов, общее количество).
        """
        products, total = await self.data_manager.get_best_selling_products(
            pagination,
            limit
        )
        return [
            ProductResponseSchema.model_validate(product) for product in products
        ], total

    async def get_top_discounts(
        self,
        pagination: PaginationParams,
        min_discount: float = 10.0,
        limit: int = 10
    ) -> Tuple[List[ProductResponseSchema], int]:
        """
        Получает список продуктов с самыми большими скидками.

        Args:
            pagination: Параметры пагинации.
            min_discount: Минимальный размер скидки для включения в список (по умолчанию 10%).
            limit: Максимальное количество продуктов (по умолчанию 10).

        Returns:
            Кортеж (список продуктов, общее количество).
        """
        products, total = await self.data_manager.get_products_with_biggest_discounts(
            pagination,
            min_discount,
            limit
        )
        return [
            ProductResponseSchema.model_validate(product) for product in products
        ], total

    async def get_new_arrivals(
        self,
        pagination: PaginationParams,
        days_threshold: int = 30,
        limit: int = 10
    ) -> Tuple[List[ProductResponseSchema], int]:
        """
        Получает список недавно добавленных продуктов (новинки).

        Args:
            pagination: Параметры пагинации.
            days_threshold: Максимальный возраст продукта в днях (по умолчанию 30).
            limit: Максимальное количество продуктов (по умолчанию 10).

        Returns:
            Кортеж (список продуктов, общее количество).
        """
        products, total = await self.data_manager.get_recently_added_products(
            pagination,
            days_threshold,
            limit
        )
        return [
            ProductResponseSchema.model_validate(product) for product in products
        ], total
