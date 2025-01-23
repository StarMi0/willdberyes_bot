__all__ = ("router", )

from aiogram import Router

from .product_router import router as product

router = Router(name=__name__)

router.include_router(product)