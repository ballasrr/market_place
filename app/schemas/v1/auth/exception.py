"""
Схемы ответов для ошибок аутентификации.

Содержит схемы для структурированных ответов при ошибках аутентификации.
"""

from typing import Any, Dict

import pytz
from pydantic import Field

from app.schemas.v1.base import ErrorResponseSchema, ErrorSchema

moscow_tz = pytz.timezone("Europe/Moscow")

EXAMPLE_TIMESTAMP = "2025-01-01T00:00:00+03:00"
EXAMPLE_REQUEST_ID = "00000000-0000-0000-0000-000000000000"


class InvalidCredentialsErrorSchema(ErrorSchema):
    """Схема ошибки неверных учетных данных"""

    detail: str = "Неверный email или пароль"
    error_type: str = "invalid_credentials"
    status_code: int = 401
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class InvalidCredentialsResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой неверных учетных данных"""

    error: InvalidCredentialsErrorSchema


class TokenExpiredErrorSchema(ErrorSchema):
    """Схема ошибки истекшего токена"""

    detail: str = "Токен просрочен"
    error_type: str = "token_expired"
    status_code: int = 419
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)
    extra: Dict[str, Any] = Field(default={"token": True})


class TokenExpiredResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой истекшего токена"""

    error: TokenExpiredErrorSchema


class TokenInvalidErrorSchema(ErrorSchema):
    """Схема ошибки недействительного токена"""

    detail: str = "Невалидный токен"
    error_type: str = "token_invalid"
    status_code: int = 422
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)
    extra: Dict[str, Any] = Field(default={"token": True})


class TokenInvalidResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой недействительного токена"""

    error: TokenInvalidErrorSchema


class TokenMissingErrorSchema(ErrorSchema):
    """Схема ошибки отсутствующего токена"""

    detail: str = "Токен отсутствует"
    error_type: str = "token_missing"
    status_code: int = 401
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)
    extra: Dict[str, Any] = Field(default={"token": True})


class TokenMissingResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой отсутствующего токена"""

    error: TokenMissingErrorSchema


class WeakPasswordErrorSchema(ErrorSchema):
    """Схема ошибки слабого пароля"""

    detail: str = "Пароль должен быть минимум 8 символов"
    error_type: str = "weak_password"
    status_code: int = 400
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class WeakPasswordResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой слабого пароля"""

    error: WeakPasswordErrorSchema


class UserInactiveErrorSchema(ErrorSchema):
    """Схема ошибки неактивного пользователя"""

    detail: str = "Аккаунт деактивирован"
    error_type: str = "user_inactive"
    status_code: int = 403
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class UserInactiveResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой неактивного пользователя"""

    error: UserInactiveErrorSchema
