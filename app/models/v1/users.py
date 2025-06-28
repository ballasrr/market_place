import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.v1.base import BaseModel

if TYPE_CHECKING:
    from app.models.v1.addresses import UserAddress
    from app.models.v1.carts import Cart
    from app.models.v1.payments import PaymentMethod


class UserRole(str, Enum):
    """
    Роли пользователей в системе.

    Определяет уровни доступа и права пользователей.
    """

    ADMIN = "admin"  # Полный доступ к системе
    MODERATOR = "moderator"  # Модерация контента, управление пользователями
    USER = "user"  # Обычные пользователи


class UserModel(BaseModel):
    """
    Основная модель пользователя системы.

    Содержит всю информацию о пользователе: от аутентификации
    до финансовых данных и настроек уведомлений.

    Attributes:
        id: UUID идентификатор пользователя
        username: Уникальное имя пользователя для входа
        email: Email адрес (уникальный)
        phone: Номер телефона (уникальный, опционально)
        hashed_password: Хешированный пароль
        role: Роль пользователя в системе

        first_name: Имя
        last_name: Фамилия
        middle_name: Отчество
        birth_date: Дата рождения
        gender: Пол пользователя
        avatar: URL аватара

        is_active: Активен ли аккаунт
        is_verified: Подтвержден ли email/телефон

        balance: Основной баланс (рубли)
        bonus_points: Бонусные баллы
        cashback_balance: Баланс кешбэка

        email_notifications: Получать уведомления на email
        sms_notifications: Получать SMS уведомления
        push_notifications: Получать push уведомления
        marketing_consent: Согласие на маркетинговые рассылки

        referral_code: Реферальный код пользователя
        referred_by_id: UUID пользователя, который пригласил

        total_orders: Общее количество заказов
        total_spent: Общая сумма потраченных денег
        last_order_date: Дата последнего заказа
        last_login: Время последнего входа
        registration_source: Источник регистрации (web, mobile, etc)
    """

    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    # Аутентификация
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)

    # Персональная информация
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    middle_name: Mapped[str] = mapped_column(nullable=True)
    birth_date: Mapped[date] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(nullable=True)
    avatar: Mapped[str] = mapped_column(nullable=True)

    # Статусы
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Финансы
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=0)
    bonus_points: Mapped[int] = mapped_column(default=0)
    cashback_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=0
    )

    # Настройки уведомлений
    email_notifications: Mapped[bool] = mapped_column(default=True)
    sms_notifications: Mapped[bool] = mapped_column(default=False)
    push_notifications: Mapped[bool] = mapped_column(default=True)
    marketing_consent: Mapped[bool] = mapped_column(default=False)

    # Реферальная система
    referral_code: Mapped[str] = mapped_column(unique=True, nullable=True)
    referred_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Статистика
    total_orders: Mapped[int] = mapped_column(default=0)
    total_spent: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=0
    )
    last_order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_source: Mapped[str] = mapped_column(nullable=True)

    # Связи
    referred_by: Mapped["UserModel"] = relationship(
        "UserModel", remote_side="UserModel.id"
    )
    addresses: Mapped[list["UserAddress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cart: Mapped["Cart"] = relationship(back_populates="user", uselist=False)
    # orders: Mapped[list["Order"]] = relationship(back_populates="user")
    # reviews: Mapped[list["ProductReview"]] = relationship(back_populates="user")
    # wishlist: Mapped[list["WishlistItem"]] = relationship(back_populates="user")
