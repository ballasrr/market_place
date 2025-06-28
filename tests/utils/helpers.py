"""Утилиты для тестов."""
import decimal
import random
import string
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar, get_type_hints

from httpx import AsyncClient

from app.models import UserRole
from app.schemas.v1.users.base import UserSchema

T = TypeVar("T")


def create_test_user_data() -> Dict[str, Any]:
    """Создает тестовые данные пользователя."""
    unique_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "username": f"testuser_{unique_suffix}",
        "email": f"test_{unique_suffix}@example.com",
        "password": "SecurePass123!",
        "phone": f"+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
    }


def assert_response_structure(
    response_data: Dict[str, Any], required_fields: List[str]
):
    """Проверяет структуру ответа API."""
    for field in required_fields:
        assert field in response_data, f"Поле '{field}' отсутствует в ответе"


async def create_authenticated_client(
    client: AsyncClient, user_data: Dict[str, Any]
) -> Dict[str, str]:
    """Создает заголовки для аутентифицированного клиента."""
    return {"Authorization": "Bearer fake_token"}


def create_mock_user_data(user_id: int = 1) -> UserSchema:
    """Создает данные мок-пользователя для тестов."""
    # Генерируем UUID на основе user_id для предсказуемости в тестах
    user_uuid = uuid.UUID(int=user_id, version=None)

    return UserSchema(
        id=user_uuid,  # Используем UUID вместо int
        username=f"user{user_id}",
        email=f"user{user_id}@example.com",
        phone=None,
        role=UserRole.USER,
        first_name=None,
        last_name=None,
        middle_name=None,
        birth_date=None,
        gender=None,
        avatar=None,
        is_active=True,
        is_verified=True,
        is_online=False,
        balance=Decimal("0.00"),
        bonus_points=0,
        cashback_balance=Decimal("0.00"),
        email_notifications=True,
        sms_notifications=False,
        push_notifications=True,
        marketing_consent=False,
        referral_code=None,
        referred_by_id=None,
        total_orders=0,
        total_spent=Decimal("0.00"),
        last_order_date=None,
        last_login=None,
        registration_source=None,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 1, 1),
    )


def create_mock_data(
    schema_class: Type[T], custom_values: Dict[str, Any] = None, id_value: int = 1
) -> T:
    """
    Создает мок-данные для тестов для любой схемы.

    Args:
        schema_class: Класс схемы для которой нужно создать мок-данные
        custom_values: Словарь с кастомными значениями полей {имя_поля: значение}
        id_value: Значение для генерации ID (если поле id присутствует)

    Returns:
        Экземпляр схемы с заполненными мок-данными
    """
    custom_values = custom_values or {}
    type_hints = get_type_hints(schema_class)
    field_values = {}

    try:
        empty_instance = schema_class.__new__(schema_class)
        for field_name in dir(empty_instance):
            if not field_name.startswith("_") and not callable(
                getattr(empty_instance, field_name, None)
            ):
                field_values[field_name] = None
    except Exception:
        field_values = {field: None for field in type_hints}

    for field_name, field_type in type_hints.items():
        if field_name in custom_values:
            continue

        if field_name == "id":
            if "UUID" in str(field_type):
                field_values[field_name] = uuid.UUID(int=id_value, version=None)
            else:
                field_values[field_name] = id_value
        elif "str" in str(field_type):
            field_values[field_name] = f"{field_name}_{id_value}"
        elif "int" in str(field_type) and "Optional" not in str(field_type):
            field_values[field_name] = 0
        elif "float" in str(field_type) and "Optional" not in str(field_type):
            field_values[field_name] = 0.0
        elif "Decimal" in str(field_type) and "Optional" not in str(field_type):
            field_values[field_name] = decimal.Decimal("0.00")
        elif "bool" in str(field_type):
            field_values[field_name] = False
        elif "datetime" in str(field_type) and "created_at" in field_name:
            field_values[field_name] = datetime(2025, 1, 1)
        elif "datetime" in str(field_type) and "updated_at" in field_name:
            field_values[field_name] = datetime(2025, 1, 1)
        elif "Enum" in str(field_type) or any(
            issubclass(field_type, Enum)
            for b in getattr(field_type, "__bases__", [])
            if hasattr(b, "__bases__")
        ):
            try:
                enum_values = list(field_type.__members__.values())
                if enum_values:
                    field_values[field_name] = enum_values[0]
            except (AttributeError, TypeError):
                pass
        elif "List" in str(field_type) or "list" in str(field_type):
            field_values[field_name] = []
        elif "Dict" in str(field_type) or "dict" in str(field_type):
            field_values[field_name] = {}

    field_values.update(custom_values)

    try:
        instance = schema_class(**field_values)
    except TypeError as e:
        missing_fields = str(e)
        raise ValueError(
            f"Не удалось создать мок-данные для {schema_class.__name__}. "
            f"Возможно, не все обязательные поля были заполнены: {missing_fields}. "
            f"Используйте custom_values для указания значений этих полей."
        )
    return instance


def generate_test_uuid(seed: int = None) -> uuid.UUID:
    """
    Генерирует тестовый UUID.

    Args:
        seed: Число для генерации предсказуемого UUID (для тестов)

    Returns:
        UUID объект
    """
    if seed is not None:
        # Создаем предсказуемый UUID на основе seed
        return uuid.UUID(int=seed, version=None)
    else:
        # Генерируем случайный UUID
        return uuid.uuid4()


def create_mock_user_dict(user_id: int = 1) -> Dict[str, Any]:
    """
    Создает словарь с данными пользователя для мокирования.

    Используется когда нужен dict, а не Pydantic модель.
    """
    user_uuid = generate_test_uuid(user_id)

    return {
        "id": str(user_uuid),  # UUID как строка
        "username": f"user{user_id}",
        "email": f"user{user_id}@example.com",
        "phone": None,
        "role": UserRole.USER.value,
        "first_name": None,
        "last_name": None,
        "middle_name": None,
        "birth_date": None,
        "gender": None,
        "avatar": None,
        "is_active": True,
        "is_verified": True,
        "is_online": False,
        "balance": "0.00",
        "bonus_points": 0,
        "cashback_balance": "0.00",
        "email_notifications": True,
        "sms_notifications": False,
        "push_notifications": True,
        "marketing_consent": False,
        "referral_code": None,
        "referred_by_id": None,
        "total_orders": 0,
        "total_spent": "0.00",
        "last_order_date": None,
        "last_login": None,
        "registration_source": None,
        "created_at": datetime(2023, 1, 1).isoformat(),
        "updated_at": datetime(2023, 1, 1).isoformat(),
    }


def create_test_user_with_uuid(**overrides) -> Dict[str, Any]:
    """
    Создает тестовые данные пользователя с UUID.

    Используется когда нужно создать пользователя с конкретным UUID.
    """
    user_data = create_test_user_data()

    if "id" not in overrides:
        overrides["id"] = str(uuid.uuid4())

    user_data.update(overrides)
    return user_data
