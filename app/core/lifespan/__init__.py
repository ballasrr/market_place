from app.core.lifespan.base import lifespan

# Экспортируем только lifespan для использования в settings.py
__all__ = ["lifespan"]
