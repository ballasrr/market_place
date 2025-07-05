from uuid import UUID

from pydantic import Field

from app.schemas.v1.base import BaseSchema


class FavoriteBaseSchema(BaseSchema):
    """
    Базовая схема для избранных товаров.
    Содержит общие поля, которые могут быть использованы в других схемах.

    Attributes:
        user_id: UUID пользователя
        product_id: UUID товара
    """
    user_id: UUID = Field(
        description="UUID пользователя, который добавил товар в избранное",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    product_id: UUID = Field(
        description="UUID товара, добавленного в избранное",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
