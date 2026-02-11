from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import MenuItem, TrainingMaterial, Test, Answer, ChecklistItem


def get_menu_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа меню (кухня/бар)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍳 Меню кухни", callback_data="menu_type:kitchen"),
                InlineKeyboardButton(text="🍹 Меню бара", callback_data="menu_type:bar"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")],
        ]
    )
    return keyboard



def get_categories_keyboard(categories: List[str], menu_type: str) -> InlineKeyboardMarkup:
    """Список категорий"""
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=category,
                callback_data=f"category:{menu_type}:{category[:50]}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back_to_types")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_items_keyboard(items: List[MenuItem], menu_type: str, category: str) -> InlineKeyboardMarkup:
    """Список позиций меню"""
    buttons = []
    for item in items:
        status_emoji = ""
        if item.status.value == "go":
            status_emoji = "🔥 "
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji}{item.name}",
                callback_data=f"item:{item.id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data=f"menu_back_to_categories:{menu_type}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
        ]
    )


def get_training_materials_keyboard(materials: List[TrainingMaterial]) -> InlineKeyboardMarkup:
    """Список обучающих материалов"""
    buttons = []
    for material in materials:
        buttons.append([
            InlineKeyboardButton(
                text=material.title,
                callback_data=f"training:{material.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mark_completed_keyboard(material_id: int) -> InlineKeyboardMarkup:
    """Кнопка отметки о прочтении материала"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отметить как изученное", callback_data=f"training_complete:{material_id}")],
            [InlineKeyboardButton(text="◀️ К списку материалов", callback_data="training_back_to_list")],
        ]
    )


def get_tests_keyboard(tests: List[Test]) -> InlineKeyboardMarkup:
    """Список тестов"""
    buttons = []
    for test in tests:
        buttons.append([
            InlineKeyboardButton(
                text=test.title,
                callback_data=f"test_select:{test.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_test_answers_keyboard(answers: List[Answer], question_id: int) -> InlineKeyboardMarkup:
    """Варианты ответов на вопрос теста"""
    buttons = []
    for answer in answers:
        buttons.append([
            InlineKeyboardButton(
                text=answer.text,
                callback_data=f"answer:{question_id}:{answer.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_item_back_keyboard(menu_type: str, category: str, item_id: int = None, is_manager: bool = False) -> InlineKeyboardMarkup:
    """Кнопка назад к списку позиций (+ загрузка фото для менеджера)"""
    buttons = []
    if is_manager and item_id:
        buttons.append([InlineKeyboardButton(
            text="📸 Загрузить фото",
            callback_data=f"menu_upload_photo:{item_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к списку",
        callback_data=f"category:{menu_type}:{category[:50]}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== ЧЕК-ЛИСТЫ ==========

def get_checklist_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Список категорий чек-листа"""
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=category,
                callback_data=f"checklist_cat:{category[:50]}",
            )
        ])

    if not buttons:
        buttons.append([
            InlineKeyboardButton(text="Чек-лист пуст", callback_data="noop")
        ])

    buttons.append([
        InlineKeyboardButton(text="📋 Показать весь чек-лист", callback_data="checklist:all")
    ])
    buttons.append([
        InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_checklist_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад к категориям чек-листа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К категориям", callback_data="checklist:back")],
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main")],
        ]
    )
