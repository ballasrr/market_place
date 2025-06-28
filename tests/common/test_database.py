"""
Тесты для работы с базой данных.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Тест подключения к базе данных."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_database_transaction(db_session: AsyncSession):
    """Тест транзакций базы данных."""
    # Пример теста с моделями
    # user = UserModel(username="Test User", email="test@example.com")
    # db_session.add(user)
    # await db_session.commit()
    #
    # result = await db_session.execute(select(UserModel).where(UserModel.email == "test@example.com"))
    # saved_user = result.scalar_one_or_none()
    # assert saved_user is not None
    # assert saved_user.name == "Test User"
