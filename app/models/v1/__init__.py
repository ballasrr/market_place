from typing import TYPE_CHECKING

from app.models.v1.base import BaseModel
from app.models.v1.users import UserRole

__all__ = ["BaseModel", "UserRole"]

if TYPE_CHECKING:
    from app.models.v1.addresses import UserAddress
    from app.models.v1.payments import PaymentMethod
    from app.models.v1.users import UserModel
