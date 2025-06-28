from starlette_admin.contrib.sqla import ModelView


class CartItemAdmin(ModelView):
    label = "Товары в корзине"
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
    ]
