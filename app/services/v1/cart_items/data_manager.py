from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Cart, CartItem, Product
from app.schemas import CartItemCreateSchema, CartItemDataSchema, CartItemUpdateSchema
from app.services.v1.base import BaseEntityManager


class CartItemDataManager(BaseEntityManager[CartItemDataSchema]):
    """
    Менеджер данных для работы с элементами корзины.
    Реализует низкоуровневые операции для работы с таблицами элементов корзины в БД.
    Обрабатывает исключения БД и преобразует их в доменные исключения.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
        schema (Type[CartItemDataSchema]): Схема сериализации данных
        model (Type[CartItem]): Модель элемента корзины
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, schema=CartItemDataSchema, model=CartItem)

    async def get_by_id(self, cart_item_id: int) -> CartItem:
        statement = select(CartItem).where(CartItem.id == cart_item_id)
        return await self.get_one(statement)

    async def add_cart_item(
        self, product: Product, cart: Cart, data: CartItemCreateSchema
    ) -> CartItem:
        cart_item_model = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=data.quantity,
        )
        return await self.add_one(cart_item_model)

    async def get_cart_items(self, cart_id: int):
        query = (
            select(CartItem)
            .options(joinedload(CartItem.product).joinedload(Product.category))
            .where(CartItem.cart_id == cart_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_product_quantity(
        self, cart_item: CartItem, data: CartItemUpdateSchema
    ) -> CartItem:
        cart_item_data_dict = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in cart_item_data_dict.items():
            setattr(cart_item, key, value)
        return await self.update_one(cart_item)

    async def delete_cart_items(
        self,
        cart_item_ids: List[int],
    ) -> None:
        statement = select(CartItem).where(CartItem.id.in_(cart_item_ids))
        cart_items = await self.get_all(statement)
        for cart_item in cart_items:
            await self.delete_item(cart_item.id)
        return cart_items
