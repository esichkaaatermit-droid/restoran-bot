from aiogram import Router

from .start import router as start_router
from .main_menu import router as main_menu_router
from .menu import router as menu_router
from .training import router as training_router
from .tests import router as tests_router
from .lists import router as lists_router
from .motivation import router as motivation_router


def setup_routers() -> Router:
    """Настройка всех роутеров"""
    router = Router()
    
    # Порядок важен: start должен быть первым для обработки /start
    router.include_router(start_router)
    router.include_router(main_menu_router)
    router.include_router(menu_router)
    router.include_router(training_router)
    router.include_router(tests_router)
    router.include_router(lists_router)
    router.include_router(motivation_router)
    
    return router


__all__ = ["setup_routers"]
