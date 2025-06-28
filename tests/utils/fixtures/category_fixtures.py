import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category


@pytest.fixture
async def test_category_data():
    return {"title": "test", "description": "test"}


@pytest.fixture
async def created_category(db_session: AsyncSession, test_category_data):
    category = Category(
        title=test_category_data["title"], description=test_category_data["description"]
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category
