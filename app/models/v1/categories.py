from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

if TYPE_CHECKING:
    from app.models.v1.products import Product


class Category(BaseModel):
    """
    Модель категории товаров.
    Содержит информацию о названии и описании категории.

    Attributes:
        title: Название категории.
        description: Описание категории.
        parent_id: ID родительской категории (если есть).
        parent: Родительская категория (если есть).
        children: Список дочерних категорий.
        products: Список продуктов, относящихся к данной категории.
    """

    __tablename__ = "categories"

    title: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=True)
    image: Mapped[str] = mapped_column(nullable=True, default=None, server_default=None)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )

    parent: Mapped["Category"] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        lazy="selectin",
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category"
    )
