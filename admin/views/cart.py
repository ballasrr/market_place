from starlette_admin.contrib.sqla import ModelView


class CartAdmin(ModelView):
    label = "Корзины"
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
    ]
