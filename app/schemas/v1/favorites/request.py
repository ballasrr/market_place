from uuid import UUID

from pydantic import Field

from app.schemas import BaseRequestSchema
from app.schemas.v1.favorites.base import FavoriteBaseSchema


class FavoriteCreateSchema(BaseRequestSchema, FavoriteBaseSchema):
    """
    Схема для добавления товара в избранное.
    Наследует все поля из FavoriteBaseSchema.
    """
    pass


class FavoriteDeleteSchema(BaseRequestSchema):
    """
    Схема для удаления товара из избранного.

    Attributes:
        product_id: UUID товара для удаления из избранного
    """
    product_id: UUID = Field(
        description="UUID товара для удаления из избранного",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
