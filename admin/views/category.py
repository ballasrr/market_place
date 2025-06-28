from starlette_admin.contrib.sqla import ModelView


class CategoryAdmin(ModelView):
    label = "Категории"
    exclude_fields_from_create = [
        "products",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_edit = [
        "products",
    ]
    exclude_fields_from_list = [
        "products",
    ]
    exclude_fields_from_details = [
        "products",
    ]
