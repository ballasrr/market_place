import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.v1.base import BaseModel

if TYPE_CHECKING:
    from app.models.v1.users import UserModel


class UserAddress(BaseModel):
    """
    Адреса пользователей для доставки.

    Хранит адресную информацию для доставки заказов.
    Поддерживает множественные адреса с возможностью выбора основного.

    Attributes:
        user_id: ID владельца адреса
        title: Название адреса ("Дом", "Работа", "Дача")

        country: Страна доставки
        region: Область/край/республика
        city: Город доставки
        street: Улица
        house: Номер дома/строения
        apartment: Номер квартиры/офиса
        entrance: Номер подъезда
        floor: Этаж
        postal_code: Почтовый индекс

        comment: Комментарий для курьера
        is_default: Используется ли адрес по умолчанию

        latitude: Широта для геолокации
        longitude: Долгота для геолокации
    """

    __tablename__ = "user_addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Название адреса
    title: Mapped[str] = mapped_column(nullable=False)  # "Дом", "Работа", "Дача"

    # Адресные данные
    country: Mapped[str] = mapped_column(nullable=False, default="Россия")
    region: Mapped[str] = mapped_column(nullable=True)  # область/край
    city: Mapped[str] = mapped_column(nullable=False)
    street: Mapped[str] = mapped_column(nullable=False)
    house: Mapped[str] = mapped_column(nullable=False)
    apartment: Mapped[str] = mapped_column(nullable=True)
    entrance: Mapped[str] = mapped_column(nullable=True)
    floor: Mapped[str] = mapped_column(nullable=True)
    postal_code: Mapped[str] = mapped_column(nullable=True)

    # Дополнительная информация
    comment: Mapped[str] = mapped_column(nullable=True)  # комментарий для курьера
    is_default: Mapped[bool] = mapped_column(default=False)

    # Координаты (для карт)
    latitude: Mapped[float] = mapped_column(nullable=True)
    longitude: Mapped[float] = mapped_column(nullable=True)

    # Связи
    user: Mapped["UserModel"] = relationship(back_populates="addresses")
