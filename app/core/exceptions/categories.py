from typing import Any, Optional

from starlette import status

from app.core.exceptions import BaseAPIException


class CategoryNotFoundError(BaseAPIException):
    """
    Исключение, которое выбрасывается, когда категория не найдена.
    Наследуется от BaseAPIException и используется для обработки ошибок
    при работе с категориями товаров в приложении.

    Attributes:
        field (Optional[str]): Поле, по которому искали категорию.
        value (Any): Значение поля, по которому искали категорию.
        detail (Optional[str]): Подробное сообщение об ошибке.
    """

    def __init__(
        self,
        field: Optional[str] = None,
        value: Any = None,
        detail: Optional[str] = None,
    ):
        message = detail or "Категория не найдена"
        if field and value is not None:
            message = f"Категория с {field}={value} не найдена"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
            error_type="category_not_found",
            extra={"field": field, "value": value} if field else None,
        )


class CategoryAlreadyExistsError(BaseAPIException):
    """
    Исключение, которое выбрасывается, когда категория уже существует.
    Наследуется от BaseAPIException и используется для обработки ошибок
    при попытке создания категории, которая уже есть в базе данных.

    Attributes:
        field (Optional[str]): Поле, по которому искали категорию.
        value (Any): Значение поля, по которому искали категорию.
        detail (Optional[str]): Подробное сообщение об ошибке.
    """

    def __init__(
        self,
        field: Optional[str] = None,
        value: Any = None,
        detail: Optional[str] = None,
    ):
        message = detail or "Категория уже существует"
        if field and value is not None:
            message = f"Категория с {field}={value} уже существует"

        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            error_type="category_already_exists",
            extra={"field": field, "value": value} if field else None,
        )
