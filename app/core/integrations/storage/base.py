"""Модуль менеджера данных для работы с S3."""

import logging
import os
import uuid
from typing import Any, List, Optional

import aiofiles  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from fastapi import UploadFile

from app.core.settings import settings


class BaseS3Storage:
    """
    Базовый класс для работы с S3.
    """

    def __init__(self, s3_client: Any):
        """
        Инициализация базового S3 хранилища.

        Args:
            s3_client: Клиент S3 для работы с хранилищем
        """
        self._client = s3_client
        self.endpoint = settings.AWS_ENDPOINT
        self.bucket_name = settings.AWS_BUCKET_NAME
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_bucket(self, bucket_name: Optional[str] = None) -> None:
        """
        Создание бакета в S3.

        Args:
            bucket_name (Optional[str]): имя бакета для создания (по умолчанию из конфигурации)
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            await self._client.create_bucket(Bucket=bucket_name)
            self.logger.info(f"Бакет {bucket_name} успешно создан")
        except ClientError as error:
            self.logger.error(f"Ошибка при создании бакета {bucket_name}: {error}")
            raise ValueError(f"Ошибка при создании бакета: {error}") from error
        except Exception as error:
            self.logger.error(
                f"Неожиданная ошибка при создании бакета {bucket_name}: {error}"
            )
            raise RuntimeError(f"Ошибка при создании бакета: {error}") from error

    async def bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """
        Проверка существования бакета.

        Args:
            bucket_name (Optional[str]): имя бакета для проверки (по умолчанию из конфигурации)

        Returns:
            bool: True если бакет существует, False в противном случае
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            await self._client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as error:
            if error.response["Error"]["Code"] == "404":
                return False
            error_message = f"Ошибка при проверке наличия бакета: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error

    async def file_exists(
        self, file_key: str, bucket_name: Optional[str] = None
    ) -> bool:
        """
        Проверка существования файла в S3.

        Args:
            file_key (str): ключ файла в S3
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            bool: True если файл существует, False в противном случае
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            await self._client.head_object(Bucket=bucket_name, Key=file_key)
            return True
        except ClientError as error:
            if error.response["Error"]["Code"] == "404":
                return False
            error_message = f"Ошибка при проверке наличия файла: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error

    async def upload_file_from_path(
        self, file_path: str, file_key: str, bucket_name: Optional[str] = None
    ) -> str:
        """
        Загрузка файла в S3 из файловой системы.

        Args:
            file_path (str): путь к файлу для загрузки
            file_key (str): ключ файла в S3
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            str: URL загруженного файла в S3
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")
        try:
            async with aiofiles.open(file=file_path, mode="rb") as file:
                await self._client.upload_fileobj(
                    Fileobj=file,
                    Bucket=bucket_name,
                    Key=file_key,
                )
                self.logger.info(f"Файл {file_path} успешно загружен как {file_key}")
                return await self.get_link_file(file_key, bucket_name)
        except ClientError as error:
            error_message = f"Ошибка при загрузке файла: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error
        except IOError as error:
            error_message = f"Ошибка при открытии файла: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error
        except Exception as error:
            error_message = f"Ошибка при загрузке файла: {error}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from error

    async def upload_file_from_content(
        self,
        file: UploadFile,
        file_key: str = "",
        file_content: Optional[bytes] = None,
        bucket_name: Optional[str] = None,
    ) -> str:
        """
        Прямая загрузка файла в S3.

        Args:
            file (UploadFile): файл для загрузки
            file_key (str): ключ файла в S3 (путь в бакете)
            file_content (Optional[bytes]): содержимое файла в виде байтового объекта
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            str: URL загруженного файла в S3
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        if file_content is None:
            file_content = await file.read()

        self.logger.debug(
            "Загрузка файла: name=%s, type=%s, size=%d, bucket=%s, key=%s",
            file.filename,
            file.content_type,
            len(file_content),
            bucket_name,
            file_key,
        )
        try:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_key = (
                f"{file_key}/{unique_filename}" if file_key else f"{unique_filename}"
            )

            response = await self._client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=file.content_type,
                ACL="public-read",
                CacheControl="max-age=31536000",
            )
            self.logger.info(f"Файл {file.filename} успешно загружен как {file_key}")
            self.logger.debug("Ответ S3(put_object): %s", response)
            return await self.get_link_file(file_key, bucket_name)
        except ClientError as error:
            self.logger.error(
                "Ошибка загрузки файла %s: %s\nДетали: %s",
                file.filename,
                error,
                (
                    error.response["Error"]
                    if hasattr(error, "response")
                    else "Нет деталей"
                ),
            )
            raise ValueError(f"Ошибка при загрузке файла: {error}") from error
        except Exception as error:
            self.logger.error(
                f"Неожиданная ошибка при загрузке файла {file.filename}: {error}"
            )
            raise RuntimeError(f"Ошибка при загрузке файла: {error}") from error

    async def get_link_file(
        self, file_key: str, bucket_name: Optional[str] = None
    ) -> str:
        """
        Получение ссылки на файл в S3.

        Args:
            file_key (str): ключ файла в S3
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            str: ссылка на файл в S3
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            if not await self.file_exists(file_key, bucket_name):
                self.logger.warning(
                    f"Запрошена ссылка на несуществующий файл: {file_key}"
                )
            return f"{self.endpoint}/{bucket_name}/{file_key}"
        except ClientError as error:
            error_message = f"Ошибка при получении ссылки на файл: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error
        except Exception as error:
            error_message = f"Ошибка при получении ссылки на файл: {error}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from error

    async def delete_file(
        self, file_key: str, bucket_name: Optional[str] = None
    ) -> bool:
        """
        Удаление файла из бакета.

        Args:
            file_key (str): ключ файла для удаления
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            bool: True если файл успешно удален
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            await self._client.delete_object(Bucket=bucket_name, Key=file_key)
            self.logger.info(f"Файл {file_key} успешно удален")
            return True
        except ClientError as error:
            error_message = f"Ошибка при удалении файла из бакета: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error
        except Exception as error:
            error_message = f"Ошибка при удалении файла из бакета: {error}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from error

    async def get_file_keys(
        self, prefix: str = "", bucket_name: Optional[str] = None
    ) -> List[str]:
        """
        Получение списка файлов в бакете.

        Args:
            prefix (str): префикс для фильтрации файлов
            bucket_name (Optional[str]): имя бакета (по умолчанию из конфигурации)

        Returns:
            List[str]: список ключей файлов в S3
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            response = await self._client.list_objects_v2(
                Bucket=bucket_name, Prefix=prefix
            )
            keys = []
            for obj in response.get("Contents", []):
                keys.append(obj["Key"])
            return keys
        except ClientError as error:
            error_message = f"Ошибка при получении списка файлов: {error}"
            self.logger.error(error_message)
            raise ValueError(error_message) from error
        except Exception as error:
            error_message = f"Ошибка при получении списка файлов: {error}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from error
