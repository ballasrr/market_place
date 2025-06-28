from pydantic import EmailStr, Field, field_validator

from app.core.security.password import BasePasswordValidator
from app.schemas.v1.base import BaseRequestSchema


class ProfileUpdateSchema(BaseRequestSchema):
    """
    Схема для представления профиля пользователя.

    Args:
        first_name (str): Имя пользователя.
        last_name (str): Фамилия пользователя.
        email (EmailStr): Электронная почта пользователя.
        phone (str): Телефон пользователя.
    """

    first_name: str = Field(min_length=0, max_length=50, description="Имя пользователя")
    last_name: str = Field(
        min_length=0, max_length=50, description="Фамилия пользователя"
    )
    email: EmailStr = Field(description="Email пользователя")
    phone: str | None = Field(
        None,
        pattern=r"^\+7\s\(\d{3}\)\s\d{3}-\d{2}-\d{2}$",
        description="Телефон в формате +7 (XXX) XXX-XX-XX",
        examples=["+7 (999) 123-45-67"],
    )


class PasswordFormSchema(BaseRequestSchema):
    """
    Схема для формы изменения пароля.

    Attributes:
        new_password (str): Новый пароль пользователя.
        confirm_password (str): Подтверждение нового пароля.
    """

    new_password: str = Field(
        ...,
        description="Новый пароль (минимум 8 символов, заглавная и строчная буква, цифра, спецсимвол)",
        alias="new_password",
    )
    confirm_password: str = Field(..., description="Подтверждение нового пароля")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v, info):
        """Проверяет сложность нового пароля."""
        validator = BasePasswordValidator()
        return validator.validate_password_strength(v)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        """Проверяет, что новый пароль и подтверждение совпадают."""
        data = info.data
        if "new_password" in data and v != data["new_password"]:
            raise ValueError("Пароли не совпадают")
        return v
