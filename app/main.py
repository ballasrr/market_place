"""
Главный модуль приложения.

Инициализирует FastAPI приложение с:
- Подключением всех роутов
- Настройкой CORS
- Middleware для логирования
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from admin.config import admin
from app.core.exceptions.handlers import register_exception_handlers
from app.core.integrations.messaging.setup import setup_messaging
from app.core.logging import setup_logging
from app.core.middlewares.activity import ActivityMiddleware
from app.core.middlewares.auth_cookie import AuthCookieMiddleware
from app.core.middlewares.logging import LoggingMiddleware
from app.core.middlewares.rate_limit import RateLimitMiddleware
from app.core.settings import settings
from app.routes.main import MainRouter
from app.routes.v1 import APIv1


def create_application() -> FastAPI:
    """
    Создает и настраивает экземпляр приложения FastAPI.
    """
    app = FastAPI(**settings.app_params)

    setup_logging()

    register_exception_handlers(app=app)

    app.add_middleware(AuthCookieMiddleware)
    app.add_middleware(ActivityMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, **settings.rate_limit_params)
    app.add_middleware(SessionMiddleware, secret_key=settings.TOKEN_SECRET_KEY)

    app.add_middleware(CORSMiddleware, **settings.cors_params)

    app.include_router(MainRouter().get_router())

    v1_router = APIv1()
    v1_router.configure_routes()
    app.include_router(v1_router.get_router(), prefix="/api/v1")

    setup_messaging(app)
    admin.mount_to(app)

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run(app, **settings.uvicorn_params)
