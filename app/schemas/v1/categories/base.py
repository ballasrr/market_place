from typing import Optional

from pydantic import Field

from app.schemas import BaseSchema


class CategoryDataSchema(BaseSchema):
    """
    Базовая схема для категорий товаров.
    Содержит общие поля, которые могут быть использованы в других схемах категорий.

    Attributes:
        id: Уникальный идентификатор категории.
        title: Название категории.
        description: Описание категории.
        created_at: Дата и время создания категории.
        updated_at: Дата и время последнего обновления категории.
    """

    title: str = Field(
        description="Название категории", examples=["Электроника", "Одежда", "Книги"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание категории",
        examples=[
            "Все виды электроники",
            "Одежда для мужчин и женщин",
            "Книги разных жанров",
        ],
    )
    image: Optional[str] = Field(
        default=None,
        description="Ссылка на изображение категории",
        examples=[
            "https://example.com/images/electronics.jpg",
            "https://example.com/images/clothing.jpg",
        ],
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="ID родительской категории",
        examples=[1, 2, None],
    )
