from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas import BaseResponseSchema, BaseSchema
from app.schemas.v1.products.response import ProductResponseSchema
from app.schemas.v1.pagination import Page


class FavoriteResponseSchema(BaseSchema):
    """
    Схема ответа для избранного товара.

    Attributes:
        id: UUID записи в избранном
        user_id: UUID пользователя
        product_id: UUID товара
        product: Полная информация о товаре
    """
    id: UUID = Field(
        description="UUID записи в избранном",
        examples=["0"]
    )
    user_id: UUID = Field(
        description="UUID пользователя",
        examples=["0"]
    )
    product_id: UUID = Field(
        description="UUID товара",
        examples=["0"]
    )
    product: Optional[ProductResponseSchema] = Field(
        default=None,
        description="Полная информация о товаре"
    )


class FavoriteListResponseSchema(BaseResponseSchema):
    """
    Схема ответа для списка избранных товаров.

    Attributes:
        message: Сообщение о результате операции
        data: Список избранных товаров с пагинацией
    """
    message: str = "Список избранных товаров успешно получен"
    data: Page[FavoriteResponseSchema]


class FavoriteSuccessResponseSchema(BaseResponseSchema):
    """
    Схема ответа для успешных операций с избранным.

    Attributes:
        message: Сообщение о результате операции
    """
    message: str = "Операция с избранным выполнена успешно"
