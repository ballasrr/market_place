import uuid

from pydantic import Field

from app.schemas import BaseSchema


class CartDataSchema(BaseSchema):
    """
    Схема данных корзины пользователя.

    Attributes:
        user_id (uuid.UUID): ID пользователя, которому принадлежит корзина.
    """

    user_id: uuid.UUID = Field(
        description="ID пользователя, которому принадлежит корзина."
    )
