from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v1.favorites import FavoriteModel
from app.services.v1.base import BaseEntityManager
from app.schemas import FavoriteBaseSchema

class FavoriteDataManager(BaseEntityManager[FavoriteBaseSchema]):
    """
    Менеджер данных для работы с избранными товарами.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=FavoriteBaseSchema ,model=FavoriteModel)

    async def add_to_favorites(self, user_id: int, product_id: int) -> None:
        """Добавляет товар в избранное пользователя."""
        favorite = FavoriteModel(user_id=user_id, product_id=product_id)
        await self.add_one(favorite)

    async def remove_from_favorites(self, user_id: int, product_id: int) -> None:
        """Удаляет товар из избранного пользователя."""
        stmt = delete(FavoriteModel).where(
            FavoriteModel.user_id == user_id,
            FavoriteModel.product_id == product_id
        )
        await self.session.execute(stmt)

    async def get_user_favorites(self, user_id: int) -> List[FavoriteModel]:
        """Получает список избранных товаров пользователя."""
        stmt = select(FavoriteModel).join(
            FavoriteModel,
            FavoriteModel.product_id == FavoriteModel.id
        ).where(FavoriteModel.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()
