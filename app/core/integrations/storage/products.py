from typing import List, Optional

from botocore.client import BaseClient
from fastapi import Depends, UploadFile

from app.core.dependencies import get_s3_client
from app.core.integrations.storage.base import BaseS3Storage


class ProductS3DataManager(BaseS3Storage):
    """
    Менеджер для работы с S3 хранилищем.
    Расширяет базовый класс для специфических нужд приложения.
    """

    def __init__(self, s3_client: BaseClient):
        super().__init__(s3_client)

    async def process_product_images(
        self,
        old_image_urls: Optional[List[str]],
        files: List[UploadFile],
        files_content: Optional[List[bytes]] = None,
    ) -> List[str]:
        """
        Процессинг изображений: удаление старых и загрузка новых

        Args:
            old_image_urls (Optional[List[str]]): Список URL старых изображений (если есть)
            files (List[UploadFile]): Новые изображения для загрузки
            files_content (Optional[List[bytes]], optional): Список байтовых представлений изображений. Defaults to None.

        Returns:
            List[str]: Список url новых изображений
        """
        # Удаляем старые изображения
        if old_image_urls:
            for old_image_url in old_image_urls:
                if (
                    old_image_url
                    and self.endpoint in old_image_url
                    and self.bucket_name in old_image_url
                ):
                    try:
                        parts = old_image_url.split(
                            f"{self.endpoint}/{self.bucket_name}/"
                        )
                        if len(parts) > 1:
                            file_key = parts[1]
                            if await self.file_exists(file_key):
                                self.logger.info(
                                    "Удаление старого изображения продукта: %s",
                                    file_key,
                                )
                                await self.delete_file(file_key)
                    except Exception as e:
                        self.logger.error(
                            "Ошибка удаления старого изображения продукта: %s", str(e)
                        )

        # Загружаем новые изображения
        image_urls = []
        if files_content is None:
            files_content = [None] * len(files)
        for file, file_content in zip(files, files_content):
            try:
                result = await self.upload_file_from_content(
                    file=file, file_content=file_content, file_key="product_images"
                )
                self.logger.info("Загружено новое изображение продукта: %s", result)
                image_urls.append(result)
            except Exception as e:
                self.logger.error(
                    "Ошибка загрузки нового изображения продукта: %s", str(e)
                )
                raise ValueError(
                    f"Не удалось загрузить файл изображения продукта: {str(e)}"
                )

        return image_urls


async def get_product_s3_manager(
    s3_client=Depends(get_s3_client),
) -> ProductS3DataManager:
    return ProductS3DataManager(s3_client)
