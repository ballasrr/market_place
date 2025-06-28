from starlette_admin.contrib.sqla import ModelView


class ProductAdmin(ModelView):
    label = "Продукты"
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
        "items",
    ]
    exclude_fields_from_list = [
        "items",
    ]
    exclude_fields_from_edit = [
        "items",
    ]
    exclude_fields_from_detail = [
        "items",
    ]
