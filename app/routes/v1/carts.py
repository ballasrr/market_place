from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.dependencies import get_db_session
from app.core.security.auth import get_current_user
from app.models import UserModel
from app.routes.base import BaseRouter
from app.schemas import CartItemCreateSchema, CartItemUpdateSchema, CartResponseSchema
from app.services.v1.carts.service import CartService


class CartRouter(BaseRouter):
    def __init__(self):
        super().__init__(prefix="carts", tags=["Carts"])

    def configure(self):
        @self.router.post(
            path="/add-to-cart",
            response_model=CartResponseSchema,
            status_code=status.HTTP_201_CREATED,
            summary="Добавление товара в корзину",
        )
        async def add_to_cart(
            data: CartItemCreateSchema,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> CartResponseSchema:
            return await CartService(session).add_product_to_cart(user, data)

        @self.router.get(
            path="",
            response_model=CartResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение корзины пользователя",
        )
        async def get_cart(
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> CartResponseSchema:
            return await CartService(session).get_by_user_id(user.id)

        @self.router.delete(
            path="/remove-product-from-cart/{cart_item_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Очистка корзины пользователя",
        )
        async def delete_cart_item(
            cart_item_id: int,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> None:
            await CartService(session).remove_product_from_cart(cart_item_id, user.id)

        @self.router.delete(
            path="/clear-cart",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Очистка корзины пользователя",
        )
        async def clear_cart(
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> None:
            await CartService(session).clear_cart(user.id)

        @self.router.put(
            path="/{cart_item_id}",
            response_model=CartResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Обновление количества товара в корзине",
        )
        async def update_cart_item(
            cart_item_id: int,
            data: CartItemUpdateSchema,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> CartResponseSchema:
            return await CartService(session).update_product_quantity(
                cart_item_id, user.id, data
            )
