from typing import AsyncGenerator

from app.core.connections.storage import S3ContextManager
from app.core.dependencies import managed_context

# Глобальный контекстный менеджер
_s3_context = S3ContextManager()


async def get_s3_client() -> AsyncGenerator:
    """
    Dependency для получения S3 клиента.

    Yields:
        S3Client: aioboto3 клиент для работы с хранилищем

    Usage в роутерах:
        ```python
        from fastapi import Depends, UploadFile

        @router.post("/upload/")
        async def upload_file(
            file: UploadFile,
            s3 = Depends(get_s3_client)
        ):
            await s3.upload_fileobj(
                file.file,
                Bucket="my-bucket",
                Key=f"uploads/{file.filename}"
            )

        @router.get("/download/{key}")
        async def download_file(
            key: str,
            s3 = Depends(get_s3_client)
        ):
            response = await s3.get_object(Bucket="my-bucket", Key=key)
            return response['Body']
        ```

    Usage в тестах:
        ```python
        @pytest.mark.asyncio
        async def test_s3_operations():
            async for s3 in get_s3_client():
                # Список объектов
                response = await s3.list_objects_v2(Bucket="test-bucket")

                # Загрузка файла
                await s3.put_object(
                    Bucket="test-bucket",
                    Key="test.txt",
                    Body=b"test content"
                )
                break
        ```
    """
    async with managed_context(_s3_context) as s3:
        yield s3
