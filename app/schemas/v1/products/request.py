from typing import Optional

from pydantic import Field

from app.schemas import BaseRequestSchema


class ProductCreateSchema(BaseRequestSchema):
    """
    Схема для создания нового продукта.
    Содержит поля, необходимые для создания продукта.

    Attributes:
        title: Название продукта.
        description: Описание продукта (необязательное).
        brand: Бренд продукта (необязательное).
        country: Страна производств�� продукта (необязательное).
        width: Ширина продукта в сантиметрах (необязательное).
        height: Высота продукта в сантиметрах (необязательное).
        material: Материал продукта (необязательное).
        price: Цена продукта.
        quantity: Количество на складе.
        category_id: ID категории, к которой принадлежит продукт (необязательное).
    """

    title: str = Field(
        description="Название продукта", examples=["Ноутбук", "Смартфон", "Книга"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание продукта",
        examples=["Мощный игровой ноутбук", "Современный смартфон", "Интересная книга"],
    )
    brand: Optional[str] = Field(
        default=None,
        description="Бренд продукта",
        examples=["Apple", "Samsung", "Sony"],
    )
    country: Optional[str] = Field(
        default=None,
        description="Страна производства продукта",
        examples=["Китай", "США", "Россия"],
    )
    width: Optional[float] = Field(
        default=None,
        description="Ширина продукта в сантиметрах",
        examples=[15.6, 5.5, 20.0],
    )
    height: Optional[float] = Field(
        default=None,
        description="Высота продукта в сантиметрах",
        examples=[10.0, 2.5, 30.0],
    )
    material: Optional[str] = Field(
        default=None,
        description="Материал продукта",
        examples=["Пластик", "Металл", "Дерево"],
    )
    price: float = Field(description="Цена продукта", examples=[999.99, 499.99, 19.99])
    quantity: int = Field(default=0, description="Количество на складе")
    category_id: Optional[int] = Field(
        default=None, description="ID категории продукта"
    )


class ProductUpdateSchema(ProductCreateSchema):
    """
    Схема для обновления продукта.
    Наследуется от ProductCreateSchema и позволяет обновлять все поля продукта.

    Attributes:
        title: Название продукта (необязательное).
        description: Описание продукта (необязательное).
        brand: Бренд продукта (необязательное).
        country: Страна производства продукта (необязательное).
        width: Ширина продукта в сантиметрах (необязательное).
        height: Высота продукта в сантиметрах (необязательное).
        material: Материал продукта (необязательное).
        price: Цена продукта (необязательное).
        quantity: Количество на складе (необязательное).
    """

    title: Optional[str] = Field(
        default=None, description="Название продукта", examples=["Ноутбук"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание продукта",
        examples=["Мощный игровой ноутбук"],
    )
    brand: Optional[str] = Field(
        default=None, description="Бренд продукта", examples=["Apple"]
    )
    country: Optional[str] = Field(
        default=None, description="Страна производства продукта", examples=["Китай"]
    )
    width: Optional[float] = Field(
        default=None, description="Ширина продукта в сантиметрах", examples=[15.6]
    )
    height: Optional[float] = Field(
        default=None, description="Высота продукта в сантиметрах", examples=[10.0]
    )
    material: Optional[str] = Field(
        default=None, description="Материал продукта", examples=["Пластик"]
    )
    price: Optional[float] = Field(
        default=None, description="Цена продукта", examples=[999.99]
    )
    quantity: Optional[int] = Field(default=None, description="Количество на складе")
    category_id: Optional[int] = Field(
        default=None, description="ID категории продукта"
    )
