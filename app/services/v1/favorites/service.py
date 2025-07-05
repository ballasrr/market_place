from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas import ProductResponseSchema
from app.services.v1.favorites.data_manager import FavoriteDataManager
from app.services.v1.products.data_manager import ProductDataManager


class FavoriteService:
    """Сервис для работы с избранными товарами."""

    def __init__(
        self,
        session: AsyncSession
    ):
        super().__init__(session)
        self.data_manager = FavoriteDataManager(session)
        self.product_data_manager = ProductDataManager(session)

    async def add_to_favorites(self, user_id: int, product_id: int) -> None:
        """Добавляет товар в избранное пользователя."""
        # Проверяем существование товара
        product = await self.product_data_manager.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        await self.data_manager.add_to_favorites(user_id, product_id)

    async def remove_from_favorites(self, user_id: int, product_id: int) -> None:
        """Удаляет товар из избранного пользователя."""
        await self.data_manager.remove_from_favorites(user_id, product_id)

    async def get_user_favorites(self, user_id: int) -> List[ProductResponseSchema]:
        """Получает список избранных товаров пользователя."""
        products = await self.data_manager.get_user_favorites(user_id)
        return [ProductResponseSchema.model_validate(product) for product in products]
