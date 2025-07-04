import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from redis import Redis

from app.core.exceptions import ForbiddenError, TokenInvalidError
from app.core.security.token import TokenManager
from app.core.settings import settings
from app.schemas import UserCredentialsSchema

from .base import BaseRedisDataManager

logger = logging.getLogger(__name__)


class AuthRedisDataManager(BaseRedisDataManager):
    """
    Redis хранилище для авторизации.

    """

    def __init__(self, redis: Redis):
        super().__init__(redis)

    async def save_token(self, user: UserCredentialsSchema, token: str) -> None:
        """
        Сохраняет токен пользователя в Redis.

        Args:
            user: Данные пользователя.
            token: Токен пользователя.

        Returns:
            None
        """
        user_data = self._prepare_user_data(user)

        await self.set(
            key=f"token:{token}",
            value=json.dumps(user_data),
            expires=TokenManager.get_token_expiration(),
        )
        await self.sadd(f"sessions:{user.email}", token)

        # Добавляем установку online статуса при входе
        await self.set_online_status(user.id, True)
        await self.update_last_activity(token)

    async def get_user_by_token(self, token: str) -> Optional[UserCredentialsSchema]:
        """
        Получает пользователя по токену.

        Args:
            token: Токен пользователя.

        Returns:
            Данные пользователя или None, если пользователь не найден.
        """
        user_data = await self.get(f"token:{token}")
        return (
            UserCredentialsSchema.model_validate_json(user_data) if user_data else None
        )

    async def remove_token(self, token: str) -> None:
        """
        Удаляет токен пользователя из Redis.

        Args:
            token: Токен пользователя.

        Returns:
            None
        """
        user_data = await self.get(f"token:{token}")
        if user_data:
            user = UserCredentialsSchema.model_validate_json(user_data)
            await self.srem(f"sessions:{user.email}", token)
        await self.delete(f"token:{token}")

    @staticmethod
    def _prepare_user_data(user: UserCredentialsSchema) -> dict:
        """
        Подготовка данных пользователя для сохранения

        Конвертируем datetime в строки для отправки в Redis,
        иначе TypeError: Object of type datetime is not JSON serializable

        Args:
            user: Данные пользователя.

        Returns:
            Данные пользователя для сохранения.
        """
        user_data = user.to_dict()
        for key, value in user_data.items():
            if isinstance(value, datetime):
                user_data[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):  # Добавляем обработку UUID
                user_data[key] = str(value)
        return user_data

    async def get_user_from_redis(
        self, token: str, email: str
    ) -> UserCredentialsSchema:
        """
        Получает пользователя из Redis или создает базовый объект

        Args:
            token: Токен пользователя.
            email: Email пользователя.

        Returns:
            Данные пользователя.
        """
        stored_token = await self.get(f"token:{token}")

        if stored_token:
            user_data = json.loads(stored_token)
            return UserCredentialsSchema.model_validate(user_data)

        return UserCredentialsSchema(email=email)

    async def verify_and_get_user(self, token: str) -> UserCredentialsSchema:
        """
        Основной метод проверки токена и получения пользователя

        Args:
            token: Токен пользователя.

        Returns:
            Данные пользователя.
        """
        logger.debug("Начало верификации токена: %s", token)

        if not token:
            logger.debug("Токен отсутствует")
            raise TokenInvalidError()
        try:
            payload = TokenManager.verify_token(token)
            logger.debug("Получен payload: %s", payload)

            email = TokenManager.validate_payload(payload)
            logger.debug("Получен email: %s", email)

            user = await self.get_user_from_redis(token, email)
            logger.debug("Получен пользователь: %s", user)
            logger.debug("Проверка активации пользователя: %s", user.is_active)

            if not user.is_active:
                raise ForbiddenError(
                    detail="Аккаунт деактивирован", extra={"user_id": user.id}
                )

            return user

        except Exception as e:
            logger.debug("Ошибка при верификации: %s", str(e))
            raise

    async def get_all_tokens(self) -> list[str]:
        """
        Получает все активные токены из Redis

        Returns:
            list[str]: Список активных токенов
        """
        # Получаем все ключи по паттерну token:*
        keys = await self.keys("token:*")

        # Убираем префикс token: из ключей
        tokens = [key.decode().split(":")[-1] for key in keys]

        return tokens

    async def update_last_activity(self, token: str) -> None:
        """
        Обновляет время последней активности пользователя

        Args:
            token: Токен пользователя

        Returns:
            None
        """
        await self.set(
            f"last_activity:{token}", str(int(datetime.now(timezone.utc).timestamp()))
        )

    async def get_last_activity(self, token: str) -> Optional[int]:
        """
        Получает время последней активности пользователя

        Args:
            token: Токен пользователя

        Returns:
            int: Время последней активности пользователя в формате timestamp (секунды)
        """
        timestamp = await self.get(f"last_activity:{token}")
        return int(timestamp) if timestamp else 0

    async def set_online_status(
        self, user_id: Union[int, uuid.UUID], is_online: bool
    ) -> None:
        """
        Устанавливает статус онлайн/офлайн пользователя

        Args:
            user_id: ID пользователя
            is_online: Статус онлайн/офлайн

        Returns:
            None
        """
        await self.set(
            key=f"online:{str(user_id)}",
            value=str(is_online),
            expires=settings.USER_INACTIVE_TIMEOUT if is_online else None,
        )

    async def get_online_status(self, user_id: Union[int, uuid.UUID]) -> bool:
        """
        Получает статус онлайн/офлайн пользователя

        Args:
            user_id: ID пользователя

        Returns:
            bool: Статус онлайн/офлайн пользователя
        """
        status = await self.get(f"online:{str(user_id)}")

        if status is None:
            return False

        if isinstance(status, bytes):
            return status.decode("utf-8") == "True"
        else:
            return status == "True"

    async def get_user_sessions(self, email: str) -> list[str]:
        """
        Получает все активные сессии пользователя

        Args:
            email: Email пользователя

        Returns:
            list[str]: Список активных токенов пользователя
        """
        return await self.smembers(f"sessions:{email}")

    async def save_refresh_token(
        self, user_id: Union[int, uuid.UUID], token: str
    ) -> None:
        """
        Сохраняет refresh токен в Redis.

        Args:
            user_id: ID пользователя
            token: Refresh токен

        Returns:
            None
        """
        # Ключ для хранения всех refresh токенов пользователя
        key = f"user:{str(user_id)}:refresh_tokens"

        # Добавляем токен в множество
        await self.sadd(key, token)

        # Устанавливаем TTL для ключа (например, 60 дней)
        from app.core.settings import settings

        await self.set_expire(key, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

    async def check_refresh_token(
        self, user_id: Union[int, uuid.UUID], token: str
    ) -> bool:
        """
        Проверяет существование refresh токена в Redis.

        Args:
            user_id: ID пользователя
            token: Refresh токен

        Returns:
            bool: True, если токен существует, иначе False
        """
        key = f"user:{str(user_id)}:refresh_tokens"

        # Проверяем наличие токена в множестве
        result = await self.sismember(key, token)
        return bool(result)

    async def remove_refresh_token(
        self, user_id: Union[int, uuid.UUID], token: str
    ) -> None:
        """
        Удаляет refresh токен из Redis.

        Args:
            user_id: ID пользователя
            token: Refresh токен

        Returns:
            None
        """
        key = f"user:{str(user_id)}:refresh_tokens"

        # Удаляем токен из множества
        await self.srem(key, token)

    async def remove_all_refresh_tokens(self, user_id: Union[int, uuid.UUID]) -> None:
        """
        Удаляет все refresh токены пользователя из Redis.

        Args:
            user_id: ID пользователя

        Returns:
            None
        """
        key = f"user:{str(user_id)}:refresh_tokens"

        # Удаляем ключ полностью
        await self.delete(key)
