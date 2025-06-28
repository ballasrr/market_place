import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

if TYPE_CHECKING:
    from app.models import UserModel
    from app.models.v1.products import Product


class Cart(BaseModel):
    """
    Модель корзины пользователя.
    """

    __tablename__ = "carts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[user_id], back_populates="cart"
    )
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        lazy="selectin",
    )


class CartItem(BaseModel):
    """
    Модель элемента корзины.
    Attributes:
        cart_id (int): ID корзины.
        product_id (int): ID продукта.
        quantity (int): Количество продукта в корзине.
    """

    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)

    cart: Mapped["Cart"] = relationship(
        "Cart",
        foreign_keys=[cart_id],
        back_populates="items",
        lazy="selectin",
    )
    product: Mapped["Product"] = relationship(
        "Product",
        foreign_keys=[product_id],
        back_populates="items",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="unique_cart_product"),
    )
