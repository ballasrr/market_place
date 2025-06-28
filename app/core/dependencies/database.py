from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connections.database import DatabaseClient

# Глобальный клиент - инициализируется один раз
database_client = DatabaseClient()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy

    Usage в роутерах:
        ```python
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select

        @router.post("/users/")
        async def create_user(
            user_data: UserCreate,
            db: AsyncSession = Depends(get_db_session)
        ):
            db.add(User(**user_data.dict())) # это пример как делать не надо :)
            await db.commit()

        @router.get("/users/{user_id}")
        async def get_user(
            user_id: uuid.UUID,
            db: AsyncSession = Depends(get_db_session)
        ):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none() # это пример как делать не надо :)
        ```

    Usage в тестах:
        ```python
        @pytest.mark.asyncio
        async def test_create_user():
            async for db in get_db_session():
                user = User(name="Test")
                db.add(user)
                await db.commit()
                break
        ```
    """
    # Получаем фабрику сессий
    session_factory = await database_client.connect()

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
