"""
Модуль для асинхронной обработки сообщений и фоновых задач.

Предоставляет интерфейс для отправки и обработки сообщений через брокер сообщений.
"""

# Импортируем API роутер для тестирования
# from .api import email_test_router
# # Импортируем и инициализируем брокер
# from .broker import broker, rabbit_router
# # Импортируем публичные классы и функции для использования в других модулях
# from .producers import EmailProducer, MessageProducer
from .categories import CategoryS3DataManager, get_category_s3_manager
from .products import ProductS3DataManager, get_product_s3_manager

__all__ = [
    # "rabbit_router",
    # "broker",
    # "MessageProducer",
    # "EmailProducer",
    # "email_test_router",
    "CategoryS3DataManager",
    "get_category_s3_manager",
    "ProductS3DataManager",
    "get_product_s3_manager",
]
