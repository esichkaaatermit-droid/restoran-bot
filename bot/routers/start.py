from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import UserRepository
from bot.keyboards.admin_keyboards import get_main_menu_keyboard
from bot.utils import get_role_name

# Путь к логотипу
LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"

router = Router()


class BindPhoneStates(StatesGroup):
    """Состояния для привязки телефона"""
    waiting_for_phone = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user=None):
    """Обработка команды /start"""

    if user:
        caption = (
            f"<b>Приветствую Вас в нашем чат-боте!</b>\n"
            f"Рады видеть Вас в команде!\n\n"
            f"👤 <b>Вы авторизованы как:</b> {user.full_name}\n"
            f"💼 <b>Должность:</b> {get_role_name(user.role)}\n"
            f"📍 <b>Филиал:</b> {user.branch}"
        )
        if LOGO_PATH.exists():
            await message.answer_photo(
                photo=FSInputFile(LOGO_PATH),
                caption=caption,
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await message.answer(
                caption,
                reply_markup=get_main_menu_keyboard(),
            )

        # Подсказка для менеджера
        if user.role.value == "manager":
            await message.answer(
                "🔑 Для доступа к панели управления используйте /admin"
            )

        await state.clear()
        return

    # Попробуем автопривязку по Telegram username
    tg_username = message.from_user.username
    if tg_username:
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            found_user = await user_repo.get_by_username_unbound(tg_username)
            if found_user:
                await user_repo.bind_telegram(found_user.id, message.from_user.id)
                caption = (
                    "✅ <b>Вы автоматически авторизованы!</b>\n"
                    "Ваш Telegram-аккаунт найден в системе.\n\n"
                    f"👤 <b>Вы авторизованы как:</b> {found_user.full_name}\n"
                    f"💼 <b>Должность:</b> {get_role_name(found_user.role)}\n"
                    f"📍 <b>Филиал:</b> {found_user.branch}"
                )
                if LOGO_PATH.exists():
                    await message.answer_photo(
                        photo=FSInputFile(LOGO_PATH),
                        caption=caption,
                        reply_markup=get_main_menu_keyboard(),
                    )
                else:
                    await message.answer(
                        caption,
                        reply_markup=get_main_menu_keyboard(),
                    )
                if found_user.role.value == "manager":
                    await message.answer(
                        "🔑 Для доступа к панели управления используйте /admin"
                    )
                await state.clear()

                # Уведомляем менеджеров
                try:
                    managers = await user_repo.get_all_with_telegram()
                    for mgr in managers:
                        if mgr.role.value == "manager" and mgr.id != found_user.id:
                            try:
                                await message.bot.send_message(
                                    mgr.telegram_id,
                                    f"ℹ️ Сотрудник <b>{found_user.full_name}</b> "
                                    f"({get_role_name(found_user.role)}) привязал Telegram.",
                                    parse_mode="HTML",
                                )
                            except Exception:
                                pass
                except Exception:
                    pass
                return

    # Если автопривязка не сработала — запрашиваем телефон
    if LOGO_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(LOGO_PATH),
            caption=(
                "<b>Добро пожаловать в Бистро ГАВРОШ!</b>\n\n"
                "Вы ещё не подключены к системе.\n"
                "Пожалуйста, введите Ваш номер телефона, "
                "который указан у администратора.\n\n"
                "Например: +7 999 123 45 67 или 89991234567"
            ),
        )
    else:
        await message.answer(
            "<b>Добро пожаловать!</b>\n\n"
            "Вы ещё не подключены к системе.\n"
            "Пожалуйста, введите Ваш номер телефона, "
            "который указан у администратора.\n\n"
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

        user = await user_repo.get_by_phone(phone)

        if user:
            await user_repo.bind_telegram(user.id, telegram_id)

            caption = (
                "✅ <b>Спасибо, доступ подтверждён!</b>\n"
                "Теперь Вы можете пользоваться ботом.\n\n"
                f"👤 <b>Вы авторизованы как:</b> {user.full_name}\n"
                f"💼 <b>Должность:</b> {get_role_name(user.role)}\n"
                f"📍 <b>Филиал:</b> {user.branch}"
            )
            if LOGO_PATH.exists():
                await message.answer_photo(
                    photo=FSInputFile(LOGO_PATH),
                    caption=caption,
                    reply_markup=get_main_menu_keyboard(),
                )
            else:
                await message.answer(
                    caption,
                    reply_markup=get_main_menu_keyboard(),
                )

            # Подсказка для менеджера
            if user.role.value == "manager":
                await message.answer(
                    "🔑 Для доступа к панели управления используйте /admin"
                )

            await state.clear()

            # Уведомляем менеджеров о новом сотруднике
            try:
                managers = await user_repo.get_all_with_telegram()
                for mgr in managers:
                    if mgr.role.value == "manager" and mgr.id != user.id:
                        try:
                            await message.bot.send_message(
                                mgr.telegram_id,
                                f"ℹ️ Сотрудник <b>{user.full_name}</b> "
                                f"({get_role_name(user.role)}) привязал Telegram.",
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass
            except Exception:
                pass
        else:
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
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await callback.message.answer(
            "Пожалуйста, используйте команду /start для начала работы."
        )
