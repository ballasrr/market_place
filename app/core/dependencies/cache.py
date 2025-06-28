from typing import AsyncGenerator

from redis import Redis

from app.core.connections import RedisContextManager
from app.core.dependencies import managed_context

# Глобальный контекстный менеджер
_redis_context = RedisContextManager()


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Dependency для получения Redis клиента.

    Yields:
        Redis: Экземпляр Redis клиента

    Usage в роутерах:
        ```python
        from fastapi import Depends
        from redis import Redis

        @router.post("/auth/")
        async def authenticate(
            redis: Redis = Depends(get_redis_client)
        ):
            await redis.set("key", "value", ex=3600)
            value = await redis.get("key")
        ```

    Usage в тестах:
        ```python
        @pytest.mark.asyncio
        async def test_redis_operations():
            async for redis in get_redis_client():
                await redis.set("test_key", "test_value")
                assert await redis.get("test_key") == b"test_value"
                break
        ```
    """
    async with managed_context(_redis_context) as redis:
        yield redis
