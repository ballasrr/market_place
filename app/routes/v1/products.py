from typing import List, Optional

from fastapi import Depends, File, UploadFile
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.dependencies import get_db_session
from app.core.integrations.storage import ProductS3DataManager, get_product_s3_manager
from app.core.security.auth import get_current_user
from app.models import UserModel
from app.routes.base import BaseRouter
from app.schemas import (
    Page,
    PaginationParams,
    ProductCreateSchema,
    ProductListResponseSchema,
    ProductResponseSchema,
    ProductUpdateSchema,
)
from app.services.v1.products.service import ProductService


class ProductRouter(BaseRouter):
    def __init__(self):
        super().__init__(prefix="products", tags=["Products"])

    def configure(self):
        @self.router.post(
            "",
            response_model=ProductResponseSchema,
            status_code=status.HTTP_201_CREATED,
            summary="Создание нового продукта",
        )
        async def create_product(
            new_product: ProductCreateSchema,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductResponseSchema:
            return await ProductService(session).create_product(user, new_product)

        @self.router.get(
            "",
            response_model=ProductListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение списка продуктов",
        )
        async def get_all_products(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            search: Optional[str] = Query(None, description="Поиск по данным продукта"),
            category_id: Optional[int] = Query(
                None, description="ID категории для фильтрации"
            ),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductListResponseSchema:
            """
            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **search**: Строка поиска по данным продукта
            * **category_id**: ID категории для фильтрации
            """
            pagination = PaginationParams(skip=skip, limit=limit)
            products, total = await ProductService(session).get_all_products(
                pagination=pagination,
                search=search,
                category_id=category_id,
            )
            page = Page(
                items=products,
                total=total,
                page=pagination.page,
                size=pagination.limit,
            )
            return ProductListResponseSchema(data=page)

        @self.router.get(
            "/{product_id}",
            response_model=ProductResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение продукта по ID",
        )
        async def get_product(
            product_id: int,
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductResponseSchema:
            return await ProductService(session).get_product_by_id(product_id)

        @self.router.delete(
            "/{product_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удаление продукта по ID",
        )
        async def delete_product(
            product_id: int,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> None:
            await ProductService(session).delete_product(user, product_id)

        @self.router.patch(
            "/{product_id}",
            response_model=ProductResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Обновление продукта по ID",
        )
        async def update_product(
            product_id: int,
            product_data: ProductUpdateSchema,
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductResponseSchema:
            return await ProductService(session).update_product(
                user, product_id, product_data
            )

        @self.router.put(
            "/{product_id}",
            response_model=ProductResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Обновление картинок продукта по ID",
        )
        async def update_product_images(
            product_id: int,
            images: List[UploadFile] = File(
                None, description="Список изображений для обновления"
            ),
            user: UserModel = Depends(get_current_user),
            session: AsyncSession = Depends(get_db_session),
            s3_data_manager: ProductS3DataManager = Depends(get_product_s3_manager),
        ) -> ProductResponseSchema:
            return await ProductService(session, s3_data_manager).update_product_images(
                user, product_id, images
            )

        @self.router.get(
            "/best-sellers",
            response_model=ProductListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение хитов продаж",
        )
        async def get_best_sellers(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            max_items: int = Query(
                10, ge=1, le=50, description="Максимальное количество хитов продаж"
            ),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductListResponseSchema:
            """
            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **max_items**: Максимальное количество возвращаемых хитов продаж (от 1 до 50)
            """
            pagination = PaginationParams(skip=skip, limit=limit)
            products, total = await ProductService(session).get_best_sellers(
                pagination=pagination,
                limit=max_items,
            )
            page = Page(
                items=products,
                total=total,
                page=pagination.page,
                size=pagination.limit,
            )
            return ProductListResponseSchema(data=page)

        @self.router.get(
            "/top-discounts",
            response_model=ProductListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение товаров с максимальными скидками",
        )
        async def get_top_discounts(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            min_discount: float = Query(
                10.0, ge=0, le=100, description="Минимальный размер скидки в процентах"
            ),
            max_items: int = Query(
                10, ge=1, le=50, description="Максимальное количество товаров"
            ),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductListResponseSchema:
            """
            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **min_discount**: Минимальный размер скидки для включения в список (0-100%)
            * **max_items**: Максимальное количество возвращаемых товаров (от 1 до 50)
            """
            pagination = PaginationParams(skip=skip, limit=limit)
            products, total = await ProductService(session).get_top_discounts(
                pagination=pagination,
                min_discount=min_discount,
                limit=max_items,
            )
            page = Page(
                items=products,
                total=total,
                page=pagination.page,
                size=pagination.limit,
            )
            return ProductListResponseSchema(data=page)

        @self.router.get(
            "/new-arrivals",
            response_model=ProductListResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Получение новинок",
        )
        async def get_new_arrivals(
            skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
            limit: int = Query(
                10, ge=1, le=100, description="Количество элементов на странице"
            ),
            days_threshold: int = Query(
                30, ge=1, description="Максимальный возраст товара в днях"
            ),
            max_items: int = Query(
                10, ge=1, le=50, description="Максимальное количество новинок"
            ),
            session: AsyncSession = Depends(get_db_session),
        ) -> ProductListResponseSchema:
            """
            ### Args:
            * **skip**: Количество пропускаемых элементов
            * **limit**: Количество элементов на странице (от 1 до 100)
            * **days_threshold**: Максимальный возраст товара для включения в список (в днях)
            * **max_items**: Максимальное количество возвращаемых новинок (от 1 до 50)
            """
            pagination = PaginationParams(skip=skip, limit=limit)
            products, total = await ProductService(session).get_new_arrivals(
                pagination=pagination,
                days_threshold=days_threshold,
                limit=max_items,
            )
            page = Page(
                items=products,
                total=total,
                page=pagination.page,
                size=pagination.limit,
            )
            return ProductListResponseSchema(data=page)
