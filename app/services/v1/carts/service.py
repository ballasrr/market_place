import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CartItemNotFoundError,
    ForbiddenError,
    OutOfStockError,
    ProductNotFoundError,
)
from app.models import UserModel
from app.schemas import (
    CartItemCreateSchema,
    CartItemResponseSchema,
    CartItemUpdateSchema,
    CartResponseSchema,
)
from app.services.v1.base import BaseService
from app.services.v1.cart_items.data_manager import CartItemDataManager
from app.services.v1.carts.data_manager import CartDataManager
from app.services.v1.products.data_manager import ProductDataManager


class CartService(BaseService):
    """
    Сервис для работы с корзинами.
    Attributes:
        session (AsyncSession): Асинхронная сессия для работы с базой данных.
        cart_data_manager (CartDataManager): Менеджер данных для операций с корзинами.
        cart_item_data_manager (CartItemDataManager): Менеджер данных для операций с товарами в корзине.
        product_data_manager (ProductDataManager): Менеджер данных для операций с продуктами.

    Methods:
        get_by_user_id: Получает корзину пользователя по его ID.
        add_product_to_cart: Добавляет продукт в корзину.
        remove_product_from_cart: Удаляет продукт из корзины.
        update_product_quantity: Обновляет количество товара в корзине.
        clear_cart: Очищает корзину пользователя.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.cart_data_manager = CartDataManager(session)
        self.cart_item_data_manager = CartItemDataManager(session)
        self.product_data_manager = ProductDataManager(session)

    async def add_product_to_cart(
        self, user: UserModel, data: CartItemCreateSchema
    ) -> CartResponseSchema:
        product = await self.product_data_manager.get_by_id(data.product_id)
        if not product:
            raise ProductNotFoundError(
                field="id", value=data.product_id, detail="Продукт не найден"
            )
        if data.quantity > product.quantity:
            raise OutOfStockError(
                detail="Недостаточно товара на складе",
                product_id=data.product_id,
                available_quantity=product.quantity,
            )
        cart, _ = await self.cart_data_manager.get_or_create(
            {"user_id": user.id}, {"user_id": user.id}
        )
        await self.cart_item_data_manager.add_cart_item(
            product=product, cart=cart, data=data
        )
        items = await self.cart_item_data_manager.get_cart_items(cart.id)
        return CartResponseSchema(
            id=cart.id,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
            user_id=user.id,
            items=[CartItemResponseSchema.model_validate(item) for item in items],
        )

    async def get_by_user_id(self, user_id: int) -> CartResponseSchema:
        cart, _ = await self.cart_data_manager.get_or_create(
            {"user_id": user_id}, {"user_id": user_id}
        )
        items = await self.cart_item_data_manager.get_cart_items(cart.id)
        return CartResponseSchema(
            id=cart.id,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
            user_id=user_id,
            items=[CartItemResponseSchema.model_validate(item) for item in items],
        )

    async def remove_product_from_cart(
        self, cart_item_id: int, user_id: uuid.UUID
    ) -> None:
        cart, _ = await self.cart_data_manager.get_or_create(
            {"user_id": user_id}, {"user_id": user_id}
        )
        cart_item = await self.cart_item_data_manager.get_by_id(cart_item_id)
        if not cart_item:
            raise CartItemNotFoundError(field="id", value=cart_item_id)
        if cart_item.cart_id != cart.id:
            raise ForbiddenError(detail="Вы не можете удалить товар из чужой корзины")
        await self.cart_item_data_manager.delete_item(cart_item.id)

    async def clear_cart(self, user_id: uuid.UUID) -> None:
        cart, _ = await self.cart_data_manager.get_or_create(
            {"user_id": user_id}, {"user_id": user_id}
        )
        items = await self.cart_item_data_manager.get_cart_items(cart.id)
        if not items:
            return
        await self.cart_item_data_manager.delete_cart_items([item.id for item in items])

    async def update_product_quantity(
        self, cart_item_id: int, user_id: uuid.UUID, data: CartItemUpdateSchema
    ) -> CartResponseSchema:
        cart, _ = await self.cart_data_manager.get_or_create(
            {"user_id": user_id}, {"user_id": user_id}
        )
        cart_item = await self.cart_item_data_manager.get_by_id(cart_item_id)
        if not cart_item:
            raise CartItemNotFoundError(field="id", value=cart_item_id)
        if cart_item.cart_id != cart.id:
            raise ForbiddenError(detail="Вы не можете обновить товар в чужой корзине")
        await self.cart_item_data_manager.update_product_quantity(cart_item, data)
        items = await self.cart_item_data_manager.get_cart_items(cart.id)
        return CartResponseSchema(
            id=cart.id,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
            user_id=user_id,
            items=[CartItemResponseSchema.model_validate(item) for item in items],
        )
