from typing import Any, Optional

from starlette import status

from app.core.exceptions import BaseAPIException


class ProductNotFoundError(BaseAPIException):
    """
    Исключение, которое выбрасывается, когда продукт не найден.
    Наследуется от BaseAPIException и используется для обработки ошибок
    при работе с продуктами в приложении.

    Attributes:
        field (Optional[str]): Поле, по которому искали продукт.
        value (Any): Значение поля, по которому искали продукт.
        detail (Optional[str]): Подробное сообщение об ошибке.
    """

    def __init__(
        self,
        field: Optional[str] = None,
        value: Any = None,
        detail: Optional[str] = None,
    ):
        message = detail or "Продукт не найден"
        if field and value is not None:
            message = f"Продукт с {field}={value} не найден"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
            error_type="product_not_found",
            extra={"field": field, "value": value} if field else None,
        )
