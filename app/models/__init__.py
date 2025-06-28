"""
Пакет моделей данных.

Предоставляет единую точку доступа ко всем моделям приложения.
"""

from app.models.v1.addresses import UserAddress
from app.models.v1.base import BaseModel
from app.models.v1.carts import Cart, CartItem
from app.models.v1.categories import Category
from app.models.v1.payments import PaymentMethod
from app.models.v1.products import Product
from app.models.v1.users import UserModel, UserRole

__all__ = [
    "BaseModel",
    "UserModel",
    "UserRole",
    "PaymentMethod",
    "UserAddress",
    "Product",
    "Cart",
    "CartItem",
    "Category",
]
