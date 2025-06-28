from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.schemas import CategoryDataSchema
from tests.utils.helpers import assert_response_structure, create_mock_data


class TestCategoryRouter:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_category(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/v1/categories",
            json={"title": "Test Category1", "description": "Test Description1"},
        )
        assert response.status_code == 201
        response_data = response.json()
        assert_response_structure(
            response_data,
            [
                "id",
                "created_at",
                "updated_at",
                "title",
                "description",
                "image",
                "parent",
                "children",
            ],
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_category_by_id(self, client: AsyncClient):
        with patch(
            "app.services.v1.categories.service.CategoryService.get_category_by_id"
        ) as mock_get_category:
            mock_category = create_mock_data(CategoryDataSchema, id_value=1)
            mock_get_category.return_value = mock_category

            response = await client.get("/api/v1/categories/1")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_categories(self, client: AsyncClient):
        with patch(
            "app.services.v1.categories.service.CategoryService.get_all_categories"
        ) as mock_get_categories:
            mock_categories = [
                create_mock_data(CategoryDataSchema, id_value=1),
                create_mock_data(CategoryDataSchema, id_value=2),
                create_mock_data(CategoryDataSchema, id_value=3),
            ]
            mock_get_categories.return_value = (mock_categories, 3)

            response = await client.get("/api/v1/categories")
            assert response.status_code == 200
            assert response.json()["data"]["total"] == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_category(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.categories.service.CategoryService.update_category"
        ) as mock_updated_category:
            mock_category = create_mock_data(
                CategoryDataSchema, {"title": "Updated Category"}, id_value=1
            )
            mock_updated_category.return_value = mock_category

            response = await auth_client.patch(
                "/api/v1/categories/1",
                data={"title": "Updated Category"},
            )

            assert response.status_code == 200
            assert response.json()["title"] == "Updated Category"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_category(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.categories.service.CategoryService.delete_category"
        ) as mock_delete_category:
            mock_delete_category.return_value = None
            response = await auth_client.delete("/api/v1/categories/1")
            assert response.status_code == 204
