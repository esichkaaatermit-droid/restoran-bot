from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import UserRepository
from bot.keyboards import get_main_menu_keyboard

router = Router()


class BindPhoneStates(StatesGroup):
    """Состояния для привязки телефона"""
    waiting_for_phone = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user=None):
    """Обработка команды /start"""
    
    if user:
        # Пользователь уже привязан - показываем главное меню
        await message.answer(
            f"Приветствую Вас в нашем чат-боте! Рады видеть Вас в команде!\n\n"
            f"Вы авторизованы как: {user.full_name}\n"
            f"Должность: {get_role_name(user.role.value)}\n"
            f"Филиал: {user.branch}",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
    else:
        # Пользователь не найден - запрашиваем телефон
        await message.answer(
            "Добро пожаловать!\n\n"
            "Вы ещё не подключены к системе. "
            "Пожалуйста, введите Ваш номер телефона, который указан у администратора.\n\n"
            "Например: +7 999 123 45 67 или 89991234567"
        )
        await state.set_state(BindPhoneStates.waiting_for_phone)


@router.message(BindPhoneStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка введённого номера телефона"""
    phone = message.text.strip()
    telegram_id = message.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        
        # Ищем пользователя с таким телефоном и без привязанного telegram_id
        user = await user_repo.get_by_phone(phone)
        
        if user:
            # Привязываем telegram_id
            await user_repo.bind_telegram(user.id, telegram_id)
            
            await message.answer(
                f"Спасибо, доступ подтверждён! Теперь Вы можете пользоваться ботом.\n\n"
                f"Приветствую Вас в нашем чат-боте! Рады видеть Вас в команде!\n\n"
                f"Вы авторизованы как: {user.full_name}\n"
                f"Должность: {get_role_name(user.role.value)}\n"
                f"Филиал: {user.branch}",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
        else:
            # Проверяем, может телефон уже привязан к другому telegram_id
            existing_user = await user_repo.get_by_phone_any(phone)
            if existing_user and existing_user.telegram_id:
                await message.answer(
                    "Этот номер телефона уже привязан к другому аккаунту Telegram. "
                    "Пожалуйста, обратитесь к Вашему менеджеру."
                )
            else:
                await message.answer(
                    "Пользователь с таким номером не найден. "
                    "Пожалуйста, обратитесь к Вашему менеджеру.\n\n"
                    "Вы можете попробовать ввести номер ещё раз или связаться с администратором."
                )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, user=None):
    """Возврат в главное меню"""
    await callback.answer()
    
    if user:
        await callback.message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.answer(
            "Пожалуйста, используйте команду /start для начала работы."
        )


def get_role_name(role: str) -> str:
    """Получить название роли на русском"""
    roles = {
        "hostess": "Хостес",
        "waiter": "Официант",
        "bartender": "Бармен",
        "manager": "Менеджер"
    }
    return roles.get(role, role)
