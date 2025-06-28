from starlette_admin.contrib.sqla import ModelView


class UserAddressAdmin(ModelView):
    label = "Адреса пользователей"
    searchable_fields = [
        "city",
        "street",
        "postal_code",
        "country",
    ]
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
    ]
