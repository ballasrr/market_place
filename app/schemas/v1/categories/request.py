from typing import Optional

from pydantic import Field

from app.schemas import BaseRequestSchema


class CategoryCreateSchema(BaseRequestSchema):
    """
    Схема для создания новой категории товаров.
    Содержит поля, необходимые для создания категории.

    Attributes:
        title: Название категории.
        description: Описание категории (необязательное).
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
    parent_id: Optional[int] = Field(
        default=None,
        description="ID родительской категории (необязательное)",
        examples=[1, 2, None],
    )


class CategoryUpdateSchema(BaseRequestSchema):
    """
    Схема для обновления существующей категории товаров.
    Содержит поля, необходимые для обновления категории.

    Attributes:
        title: Новое название категории (необ��зательное).
        description: Новое описание категории (необязательное).
        parent_id: Новый ID родительской категории (необязательное).
    """

    title: Optional[str] = Field(
        default=None,
        description="Новое название категории",
        examples=["Электроника", "Одежда", "Книги"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Новое описание категории",
        examples=[
            "Все виды электроники",
            "Одежда для мужчин и женщин",
            "Книги разных жанров",
        ],
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="Новый ID родительской категории (необязательное)",
        examples=[1, 2, None],
    )
