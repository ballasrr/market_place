from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.schemas import ProfileSchema
from app.services.v1.base import BaseEntityManager


class ProfileDataManager(BaseEntityManager[ProfileSchema]):
    """
    Класс для работы с данными пользователей в базе данных.

    Args:
        session: Асинхронная сессия для работы с базой данных.
        schema: Схема данных пользователя.
        model: Модель данных пользователя.

    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=ProfileSchema, model=UserModel)
