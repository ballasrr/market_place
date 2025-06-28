from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматического извлечения токенов из куков
    и добавления их в заголовки Authorization.
    """

    async def dispatch(self, request: Request, call_next):
        # Извлекаем токен из куки
        access_token = request.cookies.get("access_token")

        # Если токен есть и нет заголовка Authorization
        if access_token and not request.headers.get("authorization"):
            # Добавляем заголовок Authorization
            request.headers.__dict__["_list"].append(
                (b"authorization", f"Bearer {access_token}".encode())
            )

        response = await call_next(request)
        return response
