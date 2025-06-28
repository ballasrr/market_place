import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.schemas import CartDataSchema
from tests.utils.helpers import create_mock_data


class TestCartRouter:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_add_to_cart(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.carts.service.CartService.add_product_to_cart"
        ) as mock_cart_service:
            mock_cart = create_mock_data(
                CartDataSchema, custom_values={"user_id": uuid.uuid4()}, id_value=1
            )
            mock_cart_service.return_value = mock_cart
            response = await auth_client.post(
                "/api/v1/carts/add-to-cart",
                json={
                    "product_id": 1,
                    "quantity": 2,
                },
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_cart(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.carts.service.CartService.get_by_user_id"
        ) as mock_cart_service:
            mock_cart = create_mock_data(
                CartDataSchema, custom_values={"user_id": uuid.uuid4()}, id_value=1
            )
            mock_cart_service.return_value = mock_cart
            response = await auth_client.get("/api/v1/carts")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_product_from_cart(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.carts.service.CartService.remove_product_from_cart"
        ) as mock_cart_service:
            mock_cart_service.return_value = None
            response = await auth_client.delete(
                "/api/v1/carts/remove-product-from-cart/1"
            )
            assert response.status_code == 204

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_clear_cart(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.carts.service.CartService.clear_cart"
        ) as mock_cart_service:
            mock_cart_service.return_value = None
            response = await auth_client.delete("/api/v1/carts/clear-cart")
            assert response.status_code == 204

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_cart_item(self, auth_client: AsyncClient):
        with patch(
            "app.services.v1.carts.service.CartService.update_product_quantity"
        ) as mock_cart_service:
            mock_cart = create_mock_data(
                CartDataSchema, custom_values={"user_id": uuid.uuid4()}, id_value=1
            )
            mock_cart_service.return_value = mock_cart
            response = await auth_client.put("/api/v1/carts/1", json={"quantity": 3})
            assert response.status_code == 200
