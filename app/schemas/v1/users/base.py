"""
Модуль схем пользователя.

Содержит Pydantic схемы для работы с пользователями в API.
Включает схемы для различных представлений пользователя:
от базовой информации до детальных данных профиля.

Схемы организованы по принципу наследования и назначения:
- UserSchema: Полная схема со всеми полями модели
- UserPrivateSchema: Для владельца аккаунта (наследует UserSchema)
- UserPublicSchema: Публичная информация для других пользователей
- CurrentUserSchema: Минимальная схема для JWT токенов
- UserCredentialsSchema: Для внутренней аутентификации
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import EmailStr, Field

from app.models.v1.users import UserRole
from app.schemas.v1.base import CommonBaseSchema, UserBaseSchema


class UserSchema(UserBaseSchema):
    """
    Полная схема пользователя для внутренних API операций.

    Содержит все поля модели UserModel для полного представления
    пользователя в системе. Используется в сервисах и менеджерах данных.

    Attributes:
        # Основная информация
        username: Уникальное имя пользователя для входа
        email: Email адрес (валидируется)
        phone: Номер телефона (опционально)
        role: Роль в системе (по умолчанию USER)

        # Персональные данные
        first_name: Имя
        last_name: Фамилия
        middle_name: Отчество
        birth_date: Дата рождения
        gender: Пол
        avatar: URL изображения профиля

        # Статусы аккаунта
        is_active: Активен ли аккаунт (по умолчанию True)
        is_verified: Подтвержден ли email/телефон (по умолчанию False)
        is_online: Онлайн статус (опционально, для реального времени)

        # Финансы
        balance: Основной баланс счета
        bonus_points: Накопленные бонусные баллы
        cashback_balance: Баланс кешбэка

        # Настройки уведомлений
        email_notifications: Разрешены ли email уведомления
        sms_notifications: Разрешены ли SMS уведомления
        push_notifications: Разрешены ли push уведомления
        marketing_consent: Согласие на маркетинговые рассылки

        # Реферальная система
        referral_code: Персональный реферальный код
        referred_by_id: ID пользователя, который пригласил

        # Статистика активности
        total_orders: Общее количество заказов
        total_spent: Общая потраченная сумма
        last_order_date: Дата последнего заказа
        last_login: Время последнего входа в систему
        registration_source: Источник регистрации (web, mobile, etc.)

    Usage:
        ```python
        # В BaseEntityManager для валидации моделей
        user_schema = UserSchema.model_validate(user_model)

        # В сервисах для внутренних операций
        users = await user_manager.get_items()  # List[UserSchema]
        ```

    Example:
        ```python
        user = UserSchema(
            username="john_doe",
            email="john@example.com",
            first_name="John",
            role=UserRole.USER,
            balance=Decimal("100.50")
        )
        ```
    """

    # Основные поля
    username: str = Field(description="Имя пользователя")
    email: EmailStr = Field(description="Email адрес")
    phone: Optional[str] = Field(default=None, description="Номер телефона")
    role: UserRole = Field(default=UserRole.USER, description="Роль пользователя")

    # Персональная информация
    first_name: Optional[str] = Field(default=None, description="Имя")
    last_name: Optional[str] = Field(default=None, description="Фамилия")
    middle_name: Optional[str] = Field(default=None, description="Отчество")
    birth_date: Optional[date] = Field(default=None, description="Дата рождения")
    gender: Optional[str] = Field(default=None, description="Пол")
    avatar: Optional[str] = Field(default=None, description="URL аватара")

    # Статусы
    is_active: bool = Field(default=True, description="Статус активности")
    is_verified: bool = Field(default=False, description="Статус верификации")
    is_online: bool = Field(default=False, description="Статус онлайн")

    # Финансы
    balance: Decimal = Field(default=Decimal("0.00"), description="Основной баланс")
    bonus_points: int = Field(default=0, description="Бонусные баллы")
    cashback_balance: Decimal = Field(
        default=Decimal("0.00"), description="Баланс кешбэка"
    )

    # Настройки уведомлений
    email_notifications: bool = Field(default=True, description="Email уведомления")
    sms_notifications: bool = Field(default=False, description="SMS уведомления")
    push_notifications: bool = Field(default=True, description="Push уведомления")
    marketing_consent: bool = Field(default=False, description="Согласие на маркетинг")

    # Реферальная система
    referral_code: Optional[str] = Field(default=None, description="Реферальный код")
    referred_by_id: Optional[int] = Field(default=None, description="ID пригласившего")

    # Статистика
    total_orders: int = Field(default=0, description="Общее количество заказов")
    total_spent: Decimal = Field(
        default=Decimal("0.00"), description="Общая потраченная сумма"
    )
    last_order_date: Optional[datetime] = Field(
        default=None, description="Дата последнего заказа"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Время последнего входа"
    )
    registration_source: Optional[str] = Field(
        default=None, description="Источник регистрации"
    )


class UserPublicSchema(UserBaseSchema):
    """
    Публичная схема пользователя для других пользователей.

    Содержит только безопасные для публичного просмотра поля.
    Исключает персональную, финансовую и приватную информацию.

    Attributes:
        username: Имя пользователя
        avatar: URL аватара
        role: Роль пользователя
        is_active: Статус активности
        total_orders: Количество заказов (для репутации)
        created_at: Дата регистрации (наследуется от UserBaseSchema)

    Usage:
        ```python
        # GET /api/v1/users/{user_id} - публичный профиль
        @router.get("/users/{user_id}", response_model=UserPublicSchema)
        async def get_user_public_profile(user_id: uuid.UUID):
            return await user_service.get_public_profile(user_id)

        # GET /api/v1/users - список пользователей
        @router.get("/users", response_model=List[UserPublicSchema])
        async def get_users_list():
            return await user_service.get_public_users_list()
        ```
    """

    username: str = Field(description="Имя пользователя")
    avatar: Optional[str] = Field(default=None, description="URL аватара")
    role: UserRole = Field(description="Роль пользователя")
    is_active: bool = Field(description="Статус активности")
    total_orders: int = Field(default=0, description="Количество заказов")


class UserPrivateSchema(UserSchema):
    """
    Приватная схема пользователя для владельца аккаунта.

    Наследует ВСЕ поля от UserSchema без изменений.
    Используется для возврата полной информации владельцу аккаунта.

    Usage:
        ```python
        # GET /api/v1/profile - получение собственного профиля
        @router.get("/profile", response_model=UserPrivateSchema)
        async def get_my_profile(current_user: CurrentUserSchema = Depends(get_current_user)):
            return await user_service.get_private_profile(current_user.id)

        # GET /api/v1/users/me - альтернативный endpoint
        @router.get("/users/me", response_model=UserPrivateSchema)
        async def get_current_user_details(current_user: CurrentUserSchema = Depends(get_current_user)):
            return await user_service.get_user_details(current_user.id)
        ```
    """

    pass  # Наследует все поля от UserSchema


class UserProfileSchema(UserBaseSchema):
    """
    Схема для редактирования профиля пользователя.

    Содержит только поля, которые пользователь может изменять самостоятельно.
    Исключает системные поля (id, role, балансы, статистику).

    Attributes:
        # Персональная информация
        first_name: Имя
        last_name: Фамилия
        middle_name: Отчество
        birth_date: Дата рождения
        gender: Пол
        avatar: URL аватара
        phone: Номер телефона

        # Настройки уведомлений
        email_notifications: Email уведомления
        sms_notifications: SMS уведомления
        push_notifications: Push уведомления
        marketing_consent: Согласие на маркетинг

    Usage:
        ```python
        # PUT /api/v1/profile - полное обновление профиля
        @router.put("/profile", response_model=UserPrivateSchema)
        async def update_profile(
            profile_data: UserProfileSchema,
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await user_service.update_profile(current_user.id, profile_data)

        # PATCH /api/v1/profile - частичное обновление
        @router.patch("/profile", response_model=UserPrivateSchema)
        async def patch_profile(
            profile_data: UserProfileSchema,
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await user_service.patch_profile(current_user.id, profile_data)
        ```
    """

    first_name: Optional[str] = Field(default=None, description="Имя")
    last_name: Optional[str] = Field(default=None, description="Фамилия")
    middle_name: Optional[str] = Field(default=None, description="Отчество")
    birth_date: Optional[date] = Field(default=None, description="Дата рождения")
    gender: Optional[str] = Field(default=None, description="Пол")
    avatar: Optional[str] = Field(default=None, description="URL аватара")
    phone: Optional[str] = Field(default=None, description="Номер телефона")

    # Настройки уведомлений
    email_notifications: bool = Field(default=True, description="Email уведомления")
    sms_notifications: bool = Field(default=False, description="SMS уведомления")
    push_notifications: bool = Field(default=True, description="Push уведомления")
    marketing_consent: bool = Field(default=False, description="Согласие на маркетинг")


class CurrentUserSchema(CommonBaseSchema):
    """
    Схема текущего аутентифицированного пользователя.

    Минимальный набор полей для JWT токенов и зависимостей FastAPI.
    Используется в Depends(get_current_user) для получения данных
    текущего пользователя без лишней нагрузки.

    Attributes:
        id: ID пользователя
        username: Имя пользователя
        email: Email адрес
        role: Роль пользователя
        is_active: Статус активности
        is_verified: Статус верификации

    Usage:
        ```python
        # В защищенных endpoints как зависимость
        @router.get("/protected-endpoint")
        async def protected_route(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return {"message": f"Hello, {current_user.username}!"}

        # Проверка роли
        @router.get("/admin-only")
        async def admin_route(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(403, "Access denied")
            return {"admin_data": "secret"}
        ```
    """

    id: uuid.UUID = Field(description="ID пользователя")
    username: str = Field(description="Имя пользователя")
    email: EmailStr = Field(description="Email адрес")
    role: UserRole = Field(description="Роль пользователя")
    is_active: bool = Field(description="Статус активности")
    is_verified: bool = Field(description="Статус верификации")


class UserDetailDataSchema(UserBaseSchema):
    """
    Схема детальной информации о пользователе для административных целей.

    Используется администраторами для просмотра подробной информации
    о пользователях в админ-панели. Содержит расширенный набор данных
    без финансовой информации и паролей.

    Attributes:
        username: Имя пользователя
        email: Email адрес пользователя
        role: Роль пользователя в системе
        is_active: Статус активности аккаунта
        is_verified: Статус верификации
        registration_source: Источник регистрации
        last_login: Время последнего входа
        total_orders: Общее количество заказов
        created_at: Дата регистрации (наследуется от UserBaseSchema)
        updated_at: Дата последнего обновления (наследуется от UserBaseSchema)

    Usage:
        ```python
        # GET /api/v1/admin/users/{user_id} - детальная информация для админов
        @router.get("/admin/users/{user_id}", response_model=UserDetailDataSchema)
        async def get_user_details_admin(
            user_id: uuid.UUID,
            current_user: CurrentUserSchema = Depends(get_admin_user)
        ):
            return await admin_service.get_user_details(user_id)

        # GET /api/v1/admin/users - список пользователей для админ-панели
        @router.get("/admin/users", response_model=List[UserDetailDataSchema])
        async def get_users_admin(
            current_user: CurrentUserSchema = Depends(get_admin_user)
        ):
            return await admin_service.get_users_list()
        ```
    """

    username: str = Field(description="Имя пользователя")
    email: str = Field(description="Email адрес")
    role: UserRole = Field(description="Роль пользователя")
    is_active: bool = Field(default=True, description="Статус активности")
    is_verified: bool = Field(default=False, description="Статус верификации")
    registration_source: Optional[str] = Field(
        default=None, description="Источник регистрации"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Время последнего входа"
    )
    total_orders: int = Field(default=0, description="Общее количество заказов")


class UserStatusDataSchema(CommonBaseSchema):
    """
    Схема данных о статусе активности пользователя в реальном времени.

    Используется для отображения онлайн статуса пользователей
    в чатах, списках пользователей и других интерактивных элементах.
    Данные получаются из Redis кеша.

    Attributes:
        is_online: Находится ли пользователь онлайн в данный момент
        last_activity: Время последней активности в Unix timestamp

    Usage:
        ```python
        # GET /api/v1/users/{user_id}/status - статус конкретного пользователя
        @router.get("/users/{user_id}/status", response_model=UserStatusDataSchema)
        async def get_user_status(user_id: uuid.UUID):
            return await status_service.get_user_status(user_id)

        # WebSocket для реального времени
        @router.websocket("/ws/user-status")
        async def user_status_websocket(websocket: WebSocket):
            await websocket.accept()
            while True:
                status = await status_service.get_current_user_status()
                await websocket.send_json(status.model_dump())

        # В чатах для показа онлайн статуса
        @router.get("/chat/participants", response_model=List[UserStatusDataSchema])
        async def get_chat_participants_status(chat_id: int):
            return await chat_service.get_participants_status(chat_id)
        ```

    Example:
        ```python
        # Пользователь онлайн
        status = UserStatusDataSchema(
            is_online=True,
            last_activity=1642248600  # 2022-01-15 12:30:00 UTC
        )

        # Пользователь оффлайн
        status = UserStatusDataSchema(
            is_online=False,
            last_activity=1642245000  # час назад
        )
        ```
    """

    is_online: bool = Field(
        description="Находится ли пользователь онлайн в данный момент"
    )

    last_activity: Optional[int] = Field(
        default=None,
        description="Время последней активности в Unix timestamp (секунды)",
        examples=[1642248600, None],
    )


class UserCredentialsSchema(CommonBaseSchema):
    """
    Схема учетных данных пользователя для внутренней аутентификации.

    Содержит хешированный пароль и основные поля для проверки
    учетных данных. ТОЛЬКО для внутреннего использования в сервисах
    аутентификации. НЕ должна возвращаться в API ответах.

    Attributes:
        id: Уникальный идентификатор пользователя
        username: Имя пользователя
        email: Email адрес пользователя
        role: Роль пользователя в системе
        hashed_password: Хешированный пароль пользователя
        is_active: Статус активности аккаунта
        is_verified: Статус верификации email/телефона

    Usage:
        ```python
        # В AuthService для проверки паролей
        async def authenticate(self, credentials: AuthSchema):
            user_model = await self.get_user_by_identifier(credentials.username)
            user_creds = UserCredentialsSchema.model_validate(user_model)

            if not PasswordHasher.verify(user_creds.hashed_password, credentials.password):
                raise InvalidCredentialsError()

        # В TokenManager для создания JWT
        def create_payload(user_creds: UserCredentialsSchema) -> dict:
            return {
                "sub": user_creds.email,
                "user_id": user_creds.id,
                "role": user_creds.role.value
             }
        ```

    Warning:
        ⚠️ НИКОГДА не возвращайте эту схему в API ответах!
        Содержит хешированный пароль - только для внутреннего использования.
    """

    id: uuid.UUID = Field(description="Уникальный идентификатор пользователя")
    username: str = Field(description="Имя пользователя")
    email: EmailStr = Field(description="Email адрес пользователя")
    role: UserRole = Field(description="Роль пользователя")
    hashed_password: str = Field(description="Хешированный пароль")
    is_active: bool = Field(default=True, description="Статус активности")
    is_verified: bool = Field(default=False, description="Статус верификации")


class UserFinancialDataSchema(UserBaseSchema):
    """
    Схема финансовых данных пользователя.

    Содержит только финансовую информацию для специализированных
    endpoints работы с балансами, бонусами и кешбэком.
    Доступна только владельцу аккаунта и администраторам.

    Attributes:
        balance: Основной баланс счета
        bonus_points: Накопленные бонусные баллы
        cashback_balance: Баланс кешбэка
        total_spent: Общая потраченная сумма

    Usage:
        ```python
        # GET /api/v1/profile/finances - финансовая информация
        @router.get("/profile/finances", response_model=UserFinancialDataSchema)
        async def get_user_finances(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await finance_service.get_user_finances(current_user.id)

        # POST /api/v1/admin/users/{user_id}/balance - пополнение баланса админом
        @router.post("/admin/users/{user_id}/balance")
        async def add_balance(
            user_id: uuid.UUID,
            amount: Decimal,
            current_user: CurrentUserSchema = Depends(get_admin_user)
        ):
            await finance_service.add_balance(user_id, amount)
            return await finance_service.get_user_finances(user_id)
        ```
    """

    balance: Decimal = Field(default=Decimal("0.00"), description="Основной баланс")
    bonus_points: int = Field(default=0, description="Бонусные баллы")
    cashback_balance: Decimal = Field(
        default=Decimal("0.00"), description="Баланс кешбэка"
    )
    total_spent: Decimal = Field(
        default=Decimal("0.00"), description="Общая потраченная сумма"
    )


class UserNotificationSettingsSchema(UserBaseSchema):
    """
    Схема настроек уведомлений пользователя.

    Содержит только настройки уведомлений для специализированных
    endpoints управления подписками и согласиями.

    Attributes:
        email_notifications: Разрешены ли email уведомления
        sms_notifications: Разрешены ли SMS уведомления
        push_notifications: Разрешены ли push уведомления
        marketing_consent: Согласие на маркетинговые рассылки

    Usage:
        ```python
        # GET /api/v1/profile/notifications - текущие настройки
        @router.get("/profile/notifications", response_model=UserNotificationSettingsSchema)
        async def get_notification_settings(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await notification_service.get_user_settings(current_user.id)

        # PUT /api/v1/profile/notifications - обновление настроек
        @router.put("/profile/notifications", response_model=UserNotificationSettingsSchema)
        async def update_notification_settings(
            settings: UserNotificationSettingsSchema,
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await notification_service.update_settings(current_user.id, settings)
        ```
    """

    email_notifications: bool = Field(default=True, description="Email уведомления")
    sms_notifications: bool = Field(default=False, description="SMS уведомления")
    push_notifications: bool = Field(default=True, description="Push уведомления")
    marketing_consent: bool = Field(default=False, description="Согласие на маркетинг")


class UserStatsSchema(UserBaseSchema):
    """
    Схема статистики пользователя.

    Содержит аналитическую информацию о активности пользователя.
    Используется для дашбордов, отчетов и аналитики.

    Attributes:
        total_orders: Общее количество заказов
        total_spent: Общая потраченная сумма
        last_order_date: Дата последнего заказа
        last_login: Время последнего входа
        registration_source: Источник регистрации
        referral_code: Реферальный код пользователя
        referred_users_count: Количество приглашенных пользователей

    Usage:
        ```python
        # GET /api/v1/profile/stats - статистика для пользователя
        @router.get("/profile/stats", response_model=UserStatsSchema)
        async def get_user_stats(
            current_user: CurrentUserSchema = Depends(get_current_user)
        ):
            return await stats_service.get_user_stats(current_user.id)

        # GET /api/v1/admin/users/{user_id}/stats - статистика для админа
        @router.get("/admin/users/{user_id}/stats", response_model=UserStatsSchema)
        async def get_user_stats_admin(
            user_id: uuid.UUID,
            current_user: CurrentUserSchema = Depends(get_admin_user)
        ):
            return await stats_service.get_user_stats(user_id)
        ```
    """

    total_orders: int = Field(default=0, description="Общее количество заказов")
    total_spent: Decimal = Field(
        default=Decimal("0.00"), description="Общая потраченная сумма"
    )
    last_order_date: Optional[datetime] = Field(
        default=None, description="Дата последнего заказа"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Время последнего входа"
    )
    registration_source: Optional[str] = Field(
        default=None, description="Источник регистрации"
    )
    referral_code: Optional[str] = Field(default=None, description="Реферальный код")
    referred_users_count: int = Field(
        default=0, description="Количество приглашенных пользователей"
    )
