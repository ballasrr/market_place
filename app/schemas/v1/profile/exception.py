"""
Схемы ответов для ошибок, связанных с профилем пользователя.

Этот модуль содержит схемы Pydantic для структурированных ответов
при возникновении различных ошибок при работе с профилем.
"""

from pydantic import Field

from app.schemas.v1.base import ErrorResponseSchema, ErrorSchema

# Пример значений для документации
EXAMPLE_TIMESTAMP = "2025-01-01T00:00:00+03:00"
EXAMPLE_REQUEST_ID = "00000000-0000-0000-0000-000000000000"


class ProfileNotFoundErrorSchema(ErrorSchema):
    """Схема ошибки ненайденного профиля"""

    detail: str = "Профиль не найден"
    error_type: str = "profile_not_found"
    status_code: int = 404
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class ProfileNotFoundResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой ненайденного профиля"""

    error: ProfileNotFoundErrorSchema


class InvalidCurrentPasswordErrorSchema(ErrorSchema):
    """Схема ошибки неверного текущего пароля"""

    detail: str = "Текущий пароль неверен"
    error_type: str = "invalid_current_password"
    status_code: int = 400
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class InvalidCurrentPasswordResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой неверного текущего пароля"""

    error: InvalidCurrentPasswordErrorSchema


class UserNotFoundErrorSchema(ErrorSchema):
    """Схема ошибки ненайденного пользователя"""

    detail: str = "Пользователь не найден"
    error_type: str = "user_not_found"
    status_code: int = 404
    timestamp: str = Field(default=EXAMPLE_TIMESTAMP)
    request_id: str = Field(default=EXAMPLE_REQUEST_ID)


class UserNotFoundResponseSchema(ErrorResponseSchema):
    """Схема ответа с ошибкой ненайденного пользователя"""

    error: UserNotFoundErrorSchema
