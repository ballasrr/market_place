from starlette_admin.contrib.sqla import Admin

from app.core.connections.database import database_client

from .auth import CustomAuthProvider


def get_engine() -> None:
    engine = database_client.get_engine()
    return engine


admin = Admin(
    engine=get_engine(),
    title="GIDRATOP Panel",
    login_logo_url="https://storage.yandexcloud.net/gidratop-be/20112f9ca7658ca09a51023fec4769be51d19801.png",
    auth_provider=CustomAuthProvider(),
)
