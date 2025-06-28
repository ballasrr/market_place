from typing import Any, Dict, Optional

from app.core.exceptions.base import BaseAPIException


class ProfileNotFoundError(BaseAPIException):
    """
    Профиль пользователя не найден.

    Attributes:
        detail (str): Подробности об ошибке.
        extra (Optional[Dict[str, Any]]): Дополнительные данные об ошибке.
    """

    def __init__(
        self, detail: str = "Профиль не найден", extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=404, detail=detail, error_type="profile_not_found", extra=extra
        )
