from fastapi import HTTPException, Request

from app.core.security.token import TokenManager


class VerificationMiddleware:
    """
    Middleware для проверки верификации пользователей.
    """

    # Эндпоинты, доступные без верификации
    ALLOWED_UNVERIFIED_PATHS = {
        "/api/v1/verification/verify-email",
        "/api/v1/verification/resend",
        "/api/v1/verification/status",
        "/api/v1/auth/logout",
        "/api/v1/users/profile",  # Только просмотр профиля
    }

    # Эндпоинты, требующие верификации
    VERIFICATION_REQUIRED_PATHS = {
        "/api/v1/orders",
        "/api/v1/payments",
        "/api/v1/products/favorites",
        "/api/v1/users/update",
        # ...
    }

    async def __call__(self, request: Request, call_next):
        """
        Проверяет верификацию для защищенных эндпоинтов.
        """
        path = request.url.path

        # Пропускаем публичные эндпоинты
        if not self._requires_auth(path):
            return await call_next(request)

        # Получаем токен
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)

        try:
            token = TokenManager.get_token_from_header(auth_header)
            payload = TokenManager.decode_token(token)

            # Проверяем, требует ли эндпоинт верификации
            if self._requires_verification(path):
                is_limited = payload.get("limited", False)
                is_verified = not is_limited

                if not is_verified:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "message": "Требуется подтверждение email",
                            "error_type": "email_verification_required",
                            "verification_url": "/api/v1/verification/resend",
                        },
                    )

        except Exception as e:
            # Если токен невалидный, пропускаем - пусть auth middleware обработает
            pass

        return await call_next(request)

    def _requires_auth(self, path: str) -> bool:
        """Проверяет, требует ли путь аутентификации."""
        public_paths = {
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/register",
        }
        return not any(path.startswith(p) for p in public_paths)

    def _requires_verification(self, path: str) -> bool:
        """Проверяет, требует ли путь верификации email."""
        # Разрешенные без верификации
        if any(path.startswith(p) for p in self.ALLOWED_UNVERIFIED_PATHS):
            return False

        # Явно требующие верификации
        if any(path.startswith(p) for p in self.VERIFICATION_REQUIRED_PATHS):
            return True

        # По умолчанию требуем верификацию для всех остальных
        return True
