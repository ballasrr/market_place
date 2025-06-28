from typing import Optional

from pydantic import Field

from app.schemas.v1.base import BaseSchema


class ProductDataSchema(BaseSchema):
    """
    Базовая схема для продуктов.
    Содержит общие поля, которые могут быть использованы в других схемах продуктов.

    Attributes:
        title: Название продукта.
        description: Описание продукта.
        price: Цена продукта.
        brand: Бренд продукта.
        country: Страна производства продукта.
        width: Ширина продукта в сантиметрах.
        height: Высота продукта в сантиметрах.
        material: Материал продукта.
        quantity: Количество продукта на складе.
        images: Список URL изображений продукта.
    """

    title: str = Field(
        description="Название продукта", examples=["Ноутбук", "Смартфон", "Книга"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Описание продукта",
        examples=[
            "Мощный ноутбук с 16 ГБ ОЗУ",
            "Смартфон с отличной камерой",
            "Интересная книга по программированию",
        ],
    )
    price: float = Field(description="Цена продукта", examples=[999.99, 499.99, 19.99])
    brand: Optional[str] = Field(
        default=None,
        description="Бренд продукта",
        examples=["Apple", "Samsung", "Sony"],
    )
    country: Optional[str] = Field(
        default=None,
        description="Страна производства продукта",
        examples=["США", "Корея", "Япония"],
    )
    width: Optional[float] = Field(
        default=None,
        description="Ширина продукта в сантиметрах",
        examples=[30.5, 15.0, 20.0],
    )
    height: Optional[float] = Field(
        default=None,
        description="Высота продукта в сантиметрах",
        examples=[20.0, 10.0, 5.0],
    )
    material: Optional[str] = Field(
        default=None,
        description="Материал продукта",
        examples=["Пластик", "Металл", "Дерево"],
    )
    quantity: int = Field(
        default=0, description="Количество продукта на складе", examples=[100, 50, 0]
    )
    images: Optional[list[str]] = Field(
        default=None,
        description="Список URL изображений продукта",
        examples=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
    )
