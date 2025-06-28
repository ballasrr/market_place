from pydantic import Field

from app.schemas import BaseRequestSchema


class CartItemCreateSchema(BaseRequestSchema):
    """
    Схема запроса для создания элемента корзины.
    Используется для валидации входящих данных при добавлении нового элемента в корзину.
    Attributes:
        product_id (int): ID продукта, который нужно добавить в корзину.
        quantity (int): Количество добавляемого продукта.
    """

    product_id: int = Field(
        description="ID продукта, который нужно добавить в корзину."
    )
    quantity: int = Field(
        ge=1, description="Количество добавляемого продукта. Должно быть больше 0."
    )


class CartItemUpdateSchema(BaseRequestSchema):
    """
    Схема запроса для обновления элемента корзины.
    Используется для валидации входящих данных при обновлении количества товара в корзине.
    Attributes:
        quantity (int): Новое количество товара в корзине.
    """

    quantity: int = Field(
        ge=1, description="Новое количество товара в корзине. Должно быть больше 0."
    )
