from typing import List, Optional

from app.schemas import BaseResponseSchema, BaseSchema
from app.schemas.v1.pagination import Page


class CategoryResponseSchema(BaseSchema):
    """
    Схема ответа для категории товаров.
    Содержит информацию о названии и описании категории.

    Attributes:
        id (int): Уникальный идентификатор категории.
        title (str): Название категории.
        description (Optional[str]): Описание категории (необязательное поле).
        image (Optional[str]): URL изображения категории (необязательное поле).
        parent (Optional[CategoryShortResponseSchema]): Родительская категория (необязательное поле).
        children (Optional[List[CategoryShortResponseSchema]]): Список дочерних категорий (необязательное поле).
    """

    id: int
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    parent: Optional["CategoryShortResponseSchema"] = None
    children: Optional[List["CategoryShortResponseSchema"]] = None


class CategoryShortResponseSchema(BaseSchema):
    """
    Схема ответа для краткой информации о категории товаров.
    Содержит только идентификатор и название категории.

    Attributes:
        id (int): Уникальный идентификатор категории.
        title (str): Название категории.
    """

    id: int
    title: str
    image: Optional[str] = None


class CategoryListResponseSchema(BaseResponseSchema):
    """
    Схема ответа для списка категорий товаров.
    Содержит общее количество категорий и список категорий.

    Attributes:
        message (str): Сообщение о результате операции
        data (Page[CategoryResponseSchema]): Список пользователей
    """

    message: str = "Список категорий успешно получен"
    data: Page[CategoryShortResponseSchema]


class CategoryDeleteResponseSchema(BaseResponseSchema):
    """
    Схема ответа для удаления категории товаров.
    Содержит сообщение об успешном удалении категории.

    Attributes:
        message (str): Сообщение о результате операции
    """

    message: str = "Категория успешно удалена"
