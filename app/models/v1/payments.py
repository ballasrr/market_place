import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.v1.base import BaseModel

if TYPE_CHECKING:
    from app.models.v1.users import UserModel


class PaymentType(str, Enum):
    """
    Типы платежных методов.

    Определяет способы оплаты, доступные в системе.
    """

    CARD = "card"  # Банковская карта
    CASH = "cash"  # Наличные при получении
    ONLINE = "online"  # Онлайн платежи (PayPal, Яндекс.Деньги)
    WALLET = "wallet"  # Электронные кошельки


class PaymentMethod(BaseModel):
    """
    Способы оплаты пользователей.

    Хранит информацию о платежных методах, привязанных к аккаунту.
    Данные карт хранятся в зашифрованном виде или в виде токенов.

    Attributes:
        user_id: ID владельца платежного метода
        title: Название метода ("Основная карта", "Рабочая карта")
        payment_type: Тип платежного метода
        card_last_four: Последние 4 цифры карты (для отображения)
        card_brand: Платежная система (Visa, MasterCard, МИР)
        card_token: Токен от платежной системы (безопасное хранение)
        is_default: Используется ли по умолчанию
        is_active: Активен ли платежный метод
    """

    __tablename__ = "payment_methods"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Основная информация
    title: Mapped[str] = mapped_column(
        nullable=False
    )  # "Основная карта", "Рабочая карта"
    payment_type: Mapped[PaymentType] = mapped_column(nullable=False)

    # Данные карты (зашифрованные)
    card_last_four: Mapped[str] = mapped_column(nullable=True)  # последние 4 цифры
    card_brand: Mapped[str] = mapped_column(nullable=True)  # Visa, MasterCard
    card_token: Mapped[str] = mapped_column(nullable=True)  # токен платежной системы

    # Статусы
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Связи
    user: Mapped["UserModel"] = relationship(back_populates="payment_methods")
