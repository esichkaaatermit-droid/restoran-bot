from aiogram import Router

from .start import router as start_router
from .main_menu import router as main_menu_router
from .menu import router as menu_router
from .training import router as training_router
from .tests import router as tests_router
from .lists import router as lists_router
from .motivation import router as motivation_router
from .checklist import router as checklist_router

# Админские роутеры
from .admin_main import router as admin_main_router
from .admin_users import router as admin_users_router
from .admin_stopgo import router as admin_stopgo_router
from .admin_photos import router as admin_photos_router
from .admin_files import router as admin_files_router
from .admin_attest import router as admin_attest_router
from .admin_broadcast import router as admin_broadcast_router
from .admin_sync import router as admin_sync_router
from .admin_stats import router as admin_stats_router


def setup_routers() -> Router:
    """Настройка всех роутеров"""
    router = Router()

    # Порядок важен: start должен быть первым для обработки /start
    router.include_router(start_router)

    # Админские роутеры (перед пользовательскими, чтобы FSM состояния
    # админки обрабатывались приоритетнее)
    router.include_router(admin_main_router)
    router.include_router(admin_users_router)
    router.include_router(admin_stopgo_router)
    router.include_router(admin_photos_router)
    router.include_router(admin_files_router)
    router.include_router(admin_attest_router)
    router.include_router(admin_broadcast_router)
    router.include_router(admin_sync_router)
    router.include_router(admin_stats_router)

    # Пользовательские роутеры
    router.include_router(main_menu_router)
    router.include_router(menu_router)
    router.include_router(training_router)
    router.include_router(tests_router)
    router.include_router(lists_router)
    router.include_router(motivation_router)
    router.include_router(checklist_router)

    return router


__all__ = ["setup_routers"]
