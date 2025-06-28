from pydantic import Field

from app.schemas import BaseSchema
from app.schemas.v1.products import ProductDataSchema


class CartItemDataSchema(BaseSchema):
    """
    Схема данных для элемента корзины.
    Используется для сериализации и десериализации данных элемента корзины.
    Attributes:
        cart_id (int): Идентификатор корзины, к которой принадлежит элемент
        product_id (int): Идентификатор проду��та, который добавлен в корзину
        quantity (int): Количество данного продукта в корзине
    """

    cart_id: int = Field(
        description="Идентификатор корзины, к которой принадлежит элемент"
    )
    product_id: int = Field(
        description="Идентификатор продукта, который добавлен в корзину"
    )
    quantity: int = Field(description="Количество данного продукта в корзине", ge=1)
    product: "ProductDataSchema" = Field(description="Продукт, добавленный в корзину")
