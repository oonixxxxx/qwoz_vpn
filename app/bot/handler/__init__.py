from aiogram import Router

from .user_handler import user_router
from .payments_handler import payments_router
# from .other_handlers import other_router

main_router = Router()
main_router.include_router(user_router)
main_router.include_router(payments_router)
# main_router.include_router(other_router)

__all__ = ["main_router"]
