from typing import Any, Optional

from starlette import status

from app.core.exceptions import BaseAPIException


class OutOfStockError(BaseAPIException):
    """
    Исключение, возникающее при попытке добавить товар в корзину,
    когда товар отсутствует на складе.
    """

    def __init__(
        self,
        product_id: Optional[int] = None,
        available_quantity: Optional[int] = None,
        detail: Optional[str] = None,
    ):
        message = detail or "Не возможно добавить товар в корзину"
        if product_id and available_quantity is not None:
            message = (
                f"Товар с ID {product_id} отсутствует на складе,"
                f"либо его недостаточно для добавления в корзину."
                f"Доступное количество: {available_quantity}."
            )

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_type="quantity_out_of_stock",
        )


class CartItemNotFoundError(BaseAPIException):
    """
    Исключение, возникающее при попытке получить или удалить товар из корзины,
    когда товар не найден в корзине.

    Attributes:
        field (Optional[str]): Поле, по которому не найден товар.
        value (Any): Значение поля, по которому не найден товар.
        detail (Optional[str]): Дополнительное сообщение об ошибке.
    """

    def __init__(
        self,
        field: Optional[str] = None,
        value: Any = None,
        detail: Optional[str] = None,
    ):
        message = detail or "Элемент корзины не найден"
        if field and value is not None:
            message = f"Элемент корзины с {field}={value} не найден"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
            error_type="cart_item_not_found",
            extra={"field": field, "value": value} if field else None,
        )
