import uuid
from typing import List, Optional

from app.schemas import BaseSchema
from app.schemas.v1.cart_items import CartItemResponseSchema


class CartResponseSchema(BaseSchema):
    """
    Схема ответа для корзины пользователя.
    Attributes:
        id (int): ID корзины.
        created_at (str): Дата и время создания корзины.
        updated_at (str): Дата и время последнего обновления корзины.
        user_id (uuid.UUID): ID пользователя, которому при��адлежит корзина.
        items (List[CartItemResponseSchema]): Список элементов в корзине.
    """

    user_id: "uuid.UUID"
    items: Optional[List["CartItemResponseSchema"]] = None


CartItemResponseSchema.model_rebuild()
