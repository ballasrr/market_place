from pydantic import EmailStr, Field

from app.schemas.v1.base import CommonBaseSchema


class ProfileSchema(CommonBaseSchema):
    """
    Схема для представления профиля пользователя.

    Args:
        first_name (str): Имя пользователя.
        last_name (str): Фамилия пользователя.
        email (EmailStr): Электронная почта пользователя.
        phone (str): Телефон пользователя.
    """

    first_name: str | None = Field(
        None, min_length=0, max_length=50, description="Имя пользователя"
    )
    last_name: str | None = Field(
        None, min_length=0, max_length=50, description="Фамилия пользователя"
    )
    email: EmailStr = Field(description="Email пользователя")
    phone: str | None = Field(
        None,
        pattern=r"^\+7\s\(\d{3}\)\s\d{3}-\d{2}-\d{2}$",
        description="Телефон в формате +7 (XXX) XXX-XX-XX",
        examples=["+7 (999) 123-45-67"],
    )
