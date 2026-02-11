from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import UserRepository
import asyncio

from bot.keyboards.admin_keyboards import get_main_menu_keyboard
from bot.utils import get_role_name, are_tests_active
from integrations.google_sheets import GoogleSheetsSync

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
        tests_on = await are_tests_active(user.branch)
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
                reply_markup=get_main_menu_keyboard(tests_on),
            )
        else:
            await message.answer(
                caption,
                reply_markup=get_main_menu_keyboard(tests_on),
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
                tests_on = await are_tests_active(found_user.branch)
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
                        reply_markup=get_main_menu_keyboard(tests_on),
                    )
                else:
                    await message.answer(
                        caption,
                        reply_markup=get_main_menu_keyboard(tests_on),
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


@router.message(BindPhoneStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    """Обработка введённого номера телефона"""
    phone = message.text.strip()
    telegram_id = message.from_user.id

    async with async_session_maker() as session:
        user_repo = UserRepository(session)

        user = await user_repo.get_by_phone(phone)

        if user:
            # Таблица «Доступ» — источник правды: обновляем БД из таблицы
            sync = GoogleSheetsSync()
            employee = await asyncio.to_thread(sync.find_employee_by_phone, phone)
            if employee:
                await user_repo.update(
                    user.id,
                    full_name=employee["full_name"],
                    role=employee["role"],
                    branch=employee["branch"],
                    is_active=employee.get("is_active", True),
                )
                user = await user_repo.get_by_id(user.id)
                if not user or not user.is_active:
                    await message.answer(
                        "🔒 Ваш доступ временно приостановлен.\n"
                        "Если это ошибка — обратитесь к Вашему менеджеру."
                    )
                    await state.clear()
                    return

            await user_repo.bind_telegram(user.id, telegram_id)

            tests_on = await are_tests_active(user.branch)
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
                    reply_markup=get_main_menu_keyboard(tests_on),
                )
            else:
                await message.answer(
                    caption,
                    reply_markup=get_main_menu_keyboard(tests_on),
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
                    "ℹ️ Этот номер уже используется другим сотрудником.\n\n"
                    "Если Вы сменили телефон или аккаунт — попросите менеджера "
                    "обновить данные, и попробуйте снова."
                )
            else:
                # Проверяем таблицу "Доступ" — может сотрудник только что добавлен
                sync = GoogleSheetsSync()
                employee = await asyncio.to_thread(sync.find_employee_by_phone, phone)
                if employee:
                    new_user = await user_repo.create(
                        full_name=employee["full_name"],
                        phone=phone,
                        role=employee["role"],
                        branch=employee["branch"],
                        telegram_username=None,
                    )
                    await user_repo.bind_telegram(new_user.id, telegram_id)
                    tests_on = await are_tests_active(new_user.branch)
                    caption = (
                        "✅ <b>Спасибо, доступ подтверждён!</b>\n"
                        "Вы найдены в таблице сотрудников.\n\n"
                        f"👤 <b>Вы авторизованы как:</b> {new_user.full_name}\n"
                        f"💼 <b>Должность:</b> {get_role_name(new_user.role)}\n"
                        f"📍 <b>Филиал:</b> {new_user.branch}"
                    )
                    if LOGO_PATH.exists():
                        await message.answer_photo(
                            photo=FSInputFile(LOGO_PATH),
                            caption=caption,
                            reply_markup=get_main_menu_keyboard(tests_on),
                        )
                    else:
                        await message.answer(
                            caption,
                            reply_markup=get_main_menu_keyboard(tests_on),
                        )
                    if new_user.role.value == "manager":
                        await message.answer(
                            "🔑 Для доступа к панели управления используйте /admin"
                        )
                    await state.clear()
                    try:
                        managers = await user_repo.get_all_with_telegram()
                        for mgr in managers:
                            if mgr.role.value == "manager" and mgr.id != new_user.id:
                                try:
                                    await message.bot.send_message(
                                        mgr.telegram_id,
                                        f"ℹ️ Сотрудник <b>{new_user.full_name}</b> "
                                        f"({get_role_name(new_user.role)}) привязал Telegram.",
                                        parse_mode="HTML",
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass
                else:
                    await message.answer(
                        "🤔 К сожалению, мы не нашли этот номер в системе.\n\n"
                        "Попробуйте ввести номер ещё раз — возможно, была опечатка.\n"
                        "Если номер верный, обратитесь к Вашему менеджеру, "
                        "чтобы Вас добавили в таблицу сотрудников."
                    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, user=None):
    """Возврат в главное меню"""
    await callback.answer()

    if user:
        tests_on = await are_tests_active(user.branch)
        await callback.message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard(tests_on),
        )
    else:
        await callback.message.answer(
            "Пожалуйста, используйте команду /start для начала работы."
        )


@router.message(BindPhoneStates.waiting_for_phone)
async def process_phone_invalid(message: Message):
    """Fallback: отправлено не текстовое сообщение при вводе телефона"""
    await message.answer(
        "Пожалуйста, введите Ваш номер телефона текстом.\n"
        "Например: +7 999 123 45 67 или 89991234567"
    )
