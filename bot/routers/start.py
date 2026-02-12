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


async def _send_welcome(message: Message, user_obj, greeting: str, tests_on: bool):
    """Отправить приветственное сообщение с данными пользователя (одним сообщением)"""
    caption = (
        f"{greeting}\n\n"
        f"👤 <b>Вы авторизованы как:</b> {user_obj.full_name}\n"
        f"💼 <b>Должность:</b> {get_role_name(user_obj.role)}\n"
        f"📍 <b>Филиал:</b> {user_obj.branch}"
    )
    if user_obj.role.value == "manager":
        caption += "\n\n🔑 Панель управления: /admin"

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


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user=None):
    """Обработка команды /start"""

    if user:
        tests_on = await are_tests_active(user.branch)
        await _send_welcome(
            message, user,
            "<b>Приветствую Вас в нашем чат-боте!</b>\n"
            "Рады видеть Вас в команде!",
            tests_on,
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
                await _send_welcome(
                    message, found_user,
                    "✅ <b>Вы автоматически авторизованы!</b>\n"
                    "Ваш Telegram-аккаунт найден в системе.",
                    tests_on,
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

    # Если автопривязка не сработала — запрашиваем телефон или username
    auth_prompt = (
        "Вы ещё не подключены к системе.\n"
        "Пожалуйста, введите Ваш <b>номер телефона</b> или "
        "<b>Telegram-username</b> (например, @username), "
        "который указан у администратора.\n\n"
        "Примеры:\n"
        "• +7 999 123 45 67\n"
        "• 89991234567\n"
        "• @ваш_username"
    )
    if LOGO_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(LOGO_PATH),
            caption=f"<b>Добро пожаловать в Бистро ГАВРОШ!</b>\n\n{auth_prompt}",
        )
    else:
        await message.answer(
            f"<b>Добро пожаловать!</b>\n\n{auth_prompt}"
        )
    await state.set_state(BindPhoneStates.waiting_for_phone)


@router.message(BindPhoneStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    """Обработка введённого номера телефона или username"""
    raw_input = message.text.strip()
    telegram_id = message.from_user.id

    # Определяем: это username или телефон?
    digits_only = ''.join(filter(str.isdigit, raw_input))
    is_username_input = raw_input.startswith("@") or (len(digits_only) < 7 and len(raw_input) > 0)

    async with async_session_maker() as session:
        user_repo = UserRepository(session)

        user = None

        # --- Если ввели username ---
        if is_username_input:
            normalized_username = raw_input.lstrip("@").strip().lower()
            if normalized_username:
                # Ищем в БД по username (без привязки)
                user = await user_repo.get_by_username_unbound(normalized_username)
                if not user:
                    # Может быть уже привязан, но к другому telegram_id
                    user = await user_repo.get_by_username(normalized_username)
                    if user and user.telegram_id and user.telegram_id != telegram_id:
                        await message.answer(
                            "ℹ️ Этот аккаунт уже привязан к другому Telegram.\n\n"
                            "Если Вы сменили аккаунт — попросите менеджера "
                            "обновить данные, и попробуйте снова."
                        )
                        return
                if not user:
                    # Проверяем таблицу «Доступ»
                    sync = GoogleSheetsSync()
                    if await asyncio.to_thread(sync.connect):
                        employees = await asyncio.to_thread(sync.read_employees)
                        for emp in employees:
                            if emp.get("telegram_username") == normalized_username and emp.get("is_active", True):
                                user = await user_repo.create(
                                    full_name=emp["full_name"],
                                    role=emp["role"],
                                    branch=emp["branch"],
                                    telegram_username=normalized_username,
                                )
                                break

                if user:
                    await user_repo.bind_telegram(user.id, telegram_id)
                    tests_on = await are_tests_active(user.branch)
                    await _send_welcome(
                        message, user,
                        "✅ <b>Спасибо, доступ подтверждён!</b>\n"
                        "Вы найдены по Telegram-аккаунту.",
                        tests_on,
                    )
                    await state.clear()
                    # Уведомляем менеджеров
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
                    return
                else:
                    await message.answer(
                        "🤔 Мы не нашли такой Telegram-аккаунт в системе.\n\n"
                        "Попробуйте ввести <b>номер телефона</b>, "
                        "который указан у администратора.\n"
                        "Например: +7 999 123 45 67 или 89991234567\n\n"
                        "Или обратитесь к менеджеру, чтобы Вас добавили."
                    )
                    return

        # --- Стандартный поиск по телефону ---
        phone = raw_input
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
            await _send_welcome(
                message, user,
                "✅ <b>Спасибо, доступ подтверждён!</b>\n"
                "Теперь Вы можете пользоваться ботом.",
                tests_on,
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
                    await _send_welcome(
                        message, new_user,
                        "✅ <b>Спасибо, доступ подтверждён!</b>\n"
                        "Вы найдены в таблице сотрудников.",
                        tests_on,
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
    """Возврат в главное меню — удаляем inline-сообщение, Reply-клавиатура уже на месте"""
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass


@router.message(BindPhoneStates.waiting_for_phone)
async def process_phone_invalid(message: Message):
    """Fallback: отправлено не текстовое сообщение при вводе телефона"""
    await message.answer(
        "Пожалуйста, введите Ваш номер телефона текстом.\n"
        "Например: +7 999 123 45 67 или 89991234567"
    )
