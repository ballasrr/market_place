from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cart
from app.schemas import CartDataSchema
from app.services.v1.base import BaseEntityManager


class CartDataManager(BaseEntityManager[CartDataSchema]):
    """
    Менеджер данных для работы с корзинами.
    Реализует низкоуровневые операции для работы с таблицами корзин в БД.
    Обрабатывает исключения БД и преобразует их в доменные исключения.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
        schema (Type[CartDataSchema]): Схема сериализации данных
        model (Type[Cart]): Модель корзины
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=CartDataSchema, model=Cart)
