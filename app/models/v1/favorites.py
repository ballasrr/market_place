from typing import TYPE_CHECKING
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import  ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.models.v1.base import BaseModel

if TYPE_CHECKING:
    from app.models.v1.products import Product
    from app.models.v1.users import UserModel


class FavoriteModel(BaseModel):
    """
    Модель для хранения избранных товаров пользователей.

    Attributes:
        id: Целочисленный идентификатор записи (автоинкремент)
        user_id: Ссылка на пользователя (int)
        product_id: Ссылка на товар (int)

    Relationships:
        user: Связь с моделью пользователя
        product: Связь с моделью товара
    """
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    user: Mapped["UserModel"] = relationship(back_populates="favorites")
    product: Mapped["Product"] = relationship()
