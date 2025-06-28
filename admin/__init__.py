from app.models import (
    Cart,
    CartItem,
    Category,
    PaymentMethod,
    Product,
    UserAddress,
    UserModel,
)

from .config import admin
from .views.addresses import UserAddressAdmin
from .views.cart import CartAdmin
from .views.cart_item import CartItemAdmin
from .views.category import CategoryAdmin
from .views.payment_method import PaymentMethodAdmin
from .views.product import ProductAdmin
from .views.users import UserAdmin

admin.add_view(UserAdmin(model=UserModel, icon="fa-solid fa-user"))
admin.add_view(UserAddressAdmin(UserAddress, icon="fa-solid fa-map-marker-alt"))
admin.add_view(ProductAdmin(Product, icon="fa-solid fa-bottle-water"))
admin.add_view(CategoryAdmin(Category, icon="fa-solid fa-list"))
admin.add_view(PaymentMethodAdmin(PaymentMethod, icon="fa-solid fa-credit-card"))
admin.add_view(CartAdmin(Cart, icon="fa-solid fa-cart-shopping"))
admin.add_view(CartItemAdmin(CartItem, icon="fa-solid fa-cart-plus"))
