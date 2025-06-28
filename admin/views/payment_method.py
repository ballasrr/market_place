from starlette_admin.contrib.sqla import ModelView


class PaymentMethodAdmin(ModelView):
    label = "Способы оплаты"
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
    ]
