from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.schemas import ProductDataSchema
from tests.utils.helpers import create_mock_data


class TestProductRouter:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_product(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/v1/products",
            json={
                "title": "Test Product1",
                "description": "Test Description1",
                "price": 19.99,
                "quantity": 10,
            },
        )
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["title"] == "Test Product1"
        assert response_data["description"] == "Test Description1"
        assert response_data["price"] == 19.99
        assert response_data["quantity"] == 10

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_products_without_pagination(self, client: AsyncClient):
        with patch(
            "app.services.v1.products.service.ProductService.get_all_products"
        ) as mock_get_products:
            mock_products = [
                create_mock_data(ProductDataSchema, {"images": None}, id_value=1),
                create_mock_data(ProductDataSchema, {"images": None}, id_value=2),
                create_mock_data(ProductDataSchema, {"images": None}, id_value=3),
            ]
            mock_get_products.return_value = (mock_products, 3)

            response = await client.get("/api/v1/products")
            assert response.status_code == 200
            assert response.json()["data"]["total"] == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_products_with_pagination(self, client: AsyncClient):
        with patch(
            "app.services.v1.products.service.ProductService.get_all_products"
        ) as mock_get_products:
            mock_products = [
                create_mock_data(ProductDataSchema, {"images": None}, id_value=i)
                for i in range(1, 11)
            ]
            mock_get_products.return_value = (mock_products, 10)

            response = await client.get("/api/v1/products?skip=0&limit=10")
            assert response.status_code == 200
            assert len(response.json()["data"]["items"]) == 10

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_product_by_id(self, client: AsyncClient):
        with patch(
            "app.services.v1.products.service.ProductService.get_product_by_id"
        ) as mock_get_product:
            mock_product = create_mock_data(
                ProductDataSchema, {"images": None}, id_value=1
            )
            mock_get_product.return_value = mock_product

            response = await client.get("/api/v1/products/1")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_product(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.products.service.ProductService.update_product"
        ) as mock_updated_product:
            mock_product = create_mock_data(
                ProductDataSchema,
                {"title": "Updated Product", "images": None},
                id_value=1,
            )
            mock_updated_product.return_value = mock_product

            response = await auth_client.patch(
                "/api/v1/products/1",
                json={"title": "Updated Product"},
            )

            assert response.status_code == 200
            assert response.json()["title"] == "Updated Product"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_product(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.products.service.ProductService.delete_product"
        ) as mock_delete_product:
            mock_delete_product.return_value = None
            response = await auth_client.delete("/api/v1/products/1")
            assert response.status_code == 204
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_best_sellers(self, client: AsyncClient):
        """Тест для получения хитов продаж"""
        with patch(
            "app.services.v1.products.service.ProductService.get_best_sellers"
        ) as mock_get_best_sellers:
            # Создаем мок данных - 5 товаров
            mock_products = [
                create_mock_data(
                    ProductDataSchema,
                    {
                        "id": i,
                        "title": f"Best Seller {i}",
                        "price": 100.0 + i,
                        "images": None,
                        "sales_count": 50 + i  # Добавляем количество продаж
                    }
                )
                for i in range(1, 6)
            ]
            mock_get_best_sellers.return_value = (mock_products, 5)

            # Делаем запрос с параметрами
            response = await client.get(
                "/api/v1/products/best-sellers",
                params={
                    "skip": 0,
                    "limit": 10,
                    "max_items": 5
                }
            )

            # Проверяем ответ
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 5
            assert len(data["data"]["items"]) == 5
            assert data["data"]["items"][0]["title"] == "Best Seller 1"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_top_discounts(self, client: AsyncClient):
        """Тест для получения товаров с максимальными скидками"""
        with patch(
            "app.services.v1.products.service.ProductService.get_top_discounts"
        ) as mock_get_top_discounts:
            # Создаем мок данных - 3 товара со скидками
            mock_products = [
                create_mock_data(
                    ProductDataSchema,
                    {
                        "id": i,
                        "title": f"Discounted Product {i}",
                        "price": 100.0,
                        "old_price": 200.0,
                        "discount": 20.0 + i*5,  # Скидка от 20% до 30%
                        "images": None
                    }
                )
                for i in range(1, 4)
            ]
            mock_get_top_discounts.return_value = (mock_products, 3)

            response = await client.get(
                "/api/v1/products/top-discounts",
                params={
                    "skip": 0,
                    "limit": 10,
                    "min_discount": 20.0,
                    "max_items": 3
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 3
            assert len(data["data"]["items"]) == 3
            assert data["data"]["items"][0]["discount"] == 25.0  # Первый товар имеет скидку 25%

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_new_arrivals(self, client: AsyncClient):
        """Тест для получения новинок"""
        with patch(
            "app.services.v1.products.service.ProductService.get_new_arrivals"
        ) as mock_get_new_arrivals:
            # Создаем мок данных - 4 новых товара
            mock_products = [
                create_mock_data(
                    ProductDataSchema,
                    {
                        "id": i,
                        "title": f"New Product {i}",
                        "price": 50.0 + i*10,
                        "images": None,
                        "created_at": "2023-01-0{i}T00:00:00"  # Недавняя дата создания
                    }
                )
                for i in range(1, 5)
            ]
            mock_get_new_arrivals.return_value = (mock_products, 4)

            response = await client.get(
                "/api/v1/products/new-arrivals",
                params={
                    "skip": 0,
                    "limit": 10,
                    "days_threshold": 30,
                    "max_items": 4
                }
            )


            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 4
            assert len(data["data"]["items"]) == 4
            assert data["data"]["items"][0]["title"] == "New Product 1"
