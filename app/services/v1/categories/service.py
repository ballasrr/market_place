from typing import List, Optional

from botocore.exceptions import ClientError
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    InvalidFileTypeError,
    StorageError,
)
from app.core.exceptions.users import ForbiddenError
from app.core.integrations.storage import CategoryS3DataManager
from app.models import Category, UserModel
from app.schemas import (
    CategoryCreateSchema,
    CategoryResponseSchema,
    CategoryUpdateSchema,
    PaginationParams,
)
from app.services.v1.base import BaseService
from app.services.v1.categories.data_manager import CategoryDataManager


class CategoryService(BaseService):
    """
    Сервис для работы с основными категориями товаров.

    Atributes:
        session (AsyncSession): Асинхронная сессия для работы с базой данных
        data_manager (CategoryDataManager): Менеджер данных для операций с основными категориями

    Methods:
        get_all_categories: Получает все основные категории товаров
        get_category_by_id: Получает основную категорию по ID
        create_category: Создает новую основную категорию
        update_category: Обновляет существующую основную категорию
        delete__category: Удаляет основную категорию по ID
    """

    def __init__(
        self,
        session: AsyncSession,
        s3_data_manager: Optional[CategoryS3DataManager] = None,
    ):
        super().__init__(session)
        self.data_manager = CategoryDataManager(session)
        self.s3_data_manager = s3_data_manager

    async def create_category(
        self, user: UserModel, data: CategoryCreateSchema
    ) -> CategoryResponseSchema:
        existing_category = await self.data_manager.get_model_by_field(
            "title", data.title
        )
        if existing_category:
            raise CategoryAlreadyExistsError(
                field="title",
                value=data.title,
                detail="Категория с таким названием уже существует",
            )
        if data.parent_id is not None:
            parent = await self.data_manager.get_model_by_field("id", data.parent_id)
            if not parent:
                raise CategoryNotFoundError(
                    field="id",
                    value=data.parent_id,
                    detail="Родительская категория не найдена",
                )
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для создания категории",
                required_role="MODERATOR",
            )
        category = await self.data_manager.add_category(data)
        return CategoryResponseSchema.model_validate(category)

    async def update_category(
        self,
        user: UserModel,
        category_id: int,
        data: CategoryUpdateSchema,
        image: Optional[UploadFile] = None,
    ) -> CategoryResponseSchema:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для обновления категории",
                required_role="MODERATOR",
            )
        category = await self.data_manager.get_model_by_field("id", category_id)
        if not category:
            raise CategoryNotFoundError(
                field="id", value=category_id, detail="Категория не найдена"
            )
        if data.title:
            existing_category = await self.data_manager.get_model_by_field(
                "title", data.title
            )
            if existing_category and existing_category.id != category_id:
                raise CategoryAlreadyExistsError(
                    field="title",
                    value=data.title,
                    detail="Категория с таким названием уже существует",
                )
        if data.parent_id is not None:
            parent = await self.data_manager.get_model_by_field("id", data.parent_id)
            if not parent:
                raise CategoryNotFoundError(
                    field="id",
                    value=data.parent_id,
                    detail="Родительская категория не найдена",
                )
        if image:
            await self._update_category_image(category, image)
        updated_category = await self.data_manager.update_category(category, data)
        serialized_category = await self.data_manager.get_category_by_id(
            updated_category.id
        )
        return CategoryResponseSchema.model_validate(serialized_category)

    async def _update_category_image(
        self,
        category: Category,
        file: UploadFile,
    ) -> None:
        file_content = await file.read()
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise InvalidFileTypeError()
        old_image_url = None
        if hasattr(category, "image") and category.image:
            old_image_url = category.image
            self.logger.info("Текущее изображение: %s", old_image_url)
        else:
            self.logger.info("Изображение не установлено")
        try:
            image_url = await self.s3_data_manager.process_category_image(
                old_image_url=old_image_url if old_image_url else "",
                file=file,
                file_content=file_content,
            )
            self.logger.info("Файл загружен: %s", image_url)
        except ClientError as e:
            self.logger.error("Ошибка S3 при загрузке изображения: %s", str(e))
            raise StorageError(detail=f"Ошибка хранилища: {str(e)}")
        except ValueError as e:
            self.logger.error("Ошибка валидации при загрузке изображения: %s", str(e))
            raise StorageError(detail=str(e))
        except Exception as e:
            self.logger.error("Неизвестная ошибка при загрузке изображения: %s", str(e))
            raise StorageError(detail=f"Ошибка при загрузке изображения: {str(e)}")

        await self.data_manager.update_image(category, image_url)

    async def get_all_categories(
        self,
        pagination: PaginationParams,
        search: str = None,
    ) -> List[CategoryResponseSchema]:
        categories, total = await self.data_manager.get_all_categories(
            pagination=pagination,
            search=search,
        )
        return [CategoryResponseSchema.model_validate(cat) for cat in categories], total

    async def get_category_by_id(self, category_id: int) -> CategoryResponseSchema:
        category = await self.data_manager.get_category_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(
                field="id", value=category_id, detail="Категория не найдена"
            )
        return CategoryResponseSchema.model_validate(category)

    async def delete_category(self, user: UserModel, category_id: int) -> None:
        if not user.role.MODERATOR:
            raise ForbiddenError(
                detail="Недостаточно прав для обновления категории",
                required_role="MODERATOR",
            )
        category = await self.data_manager.get_category_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(
                field="id", value=category_id, detail="Категория не найдена"
            )
        await self.data_manager.delete_item(category_id)
