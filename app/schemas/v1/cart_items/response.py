from app.schemas import BaseSchema
from app.schemas.v1.products import ProductResponseSchema


class CartItemResponseSchema(BaseSchema):
    """
    Схема ответа для элемента корзины.
    Attributes:
        id (int): ID элемента корзины.
        created_at (str): Дата и время создания элемента корзины.
        updated_at (str): Дата и время последнего обновления элемента корзины.
        quantity (int): Количество продукта в корзине.
        product(ProductResponseSchema): Информация о продукте в элементе корзины.
    """

    quantity: int
    product: "ProductResponseSchema"


CartItemResponseSchema.model_rebuild()
