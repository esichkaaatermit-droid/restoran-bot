import asyncio
from typing import Dict, List, Any

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import TestRepository
from database.models import Question
from bot.keyboards import (
    get_tests_keyboard,
    get_test_answers_keyboard,
    get_back_keyboard,
)

router = Router()


class TestStates(StatesGroup):
    """Состояния для прохождения теста"""
    in_progress = State()


# Хранение активных тестов и таймеров
active_tests: Dict[int, Dict[str, Any]] = {}


async def show_tests(message: Message, user):
    """Показать список тестов"""
    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        tests = await test_repo.get_tests_by_role(user.role, user.branch)
    
    if not tests:
        await message.answer(
            "Для Вашей должности пока нет доступных тестов.\n"
            "Пожалуйста, обратитесь к менеджеру."
        )
        return
    
    await message.answer(
        "📝 <b>Аттестация</b>\n\n"
        "Выберите тест для прохождения:",
        reply_markup=get_tests_keyboard(tests),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("test_select:"))
async def start_test(callback: CallbackQuery, state: FSMContext, user=None):
    """Начать тест"""
    await callback.answer()
    
    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return
    
    test_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        
        # Проверяем количество попыток
        attempts = await test_repo.get_user_attempts(user.id, test_id)
        test = await test_repo.get_test_with_questions(test_id)
        
        if not test:
            await callback.message.edit_text(
                "Тест не найден.",
                reply_markup=get_back_keyboard("tests_back_to_list")
            )
            return
        
        if attempts >= test.max_attempts:
            await callback.message.edit_text(
                f"Вы исчерпали все попытки ({test.max_attempts}) для этого теста.\n"
                "Пожалуйста, обратитесь к менеджеру.",
                reply_markup=get_back_keyboard("tests_back_to_list")
            )
            return
        
        if not test.questions:
            await callback.message.edit_text(
                "В этом тесте пока нет вопросов.",
                reply_markup=get_back_keyboard("tests_back_to_list")
            )
            return
    
    # Сортируем вопросы по порядку
    questions = sorted(test.questions, key=lambda q: q.order_num)
    
    # Инициализируем тест
    user_id = callback.from_user.id
    active_tests[user_id] = {
        "test_id": test_id,
        "test": test,
        "questions": questions,
        "current_index": 0,
        "correct_answers": 0,
        "total_questions": len(questions),
        "answers": [],
        "message": callback.message,
        "time_per_question": test.time_per_question,
        "timer_task": None,
    }
    
    await state.set_state(TestStates.in_progress)
    
    # Показываем информацию о тесте и первый вопрос
    await callback.message.edit_text(
        f"📝 <b>{test.title}</b>\n\n"
        f"Попытка {attempts + 1} из {test.max_attempts}\n"
        f"Вопросов: {len(questions)}\n"
        f"Время на вопрос: {test.time_per_question} секунд\n"
        f"Проходной балл: {test.passing_score}%\n\n"
        "Тест начинается...",
        parse_mode="HTML"
    )
    
    await asyncio.sleep(2)
    await show_question(callback.message.bot, user_id)


async def show_question(bot: Bot, user_id: int):
    """Показать текущий вопрос"""
    if user_id not in active_tests:
        return
    
    test_data = active_tests[user_id]
    
    # Отменяем предыдущий таймер если есть
    if test_data.get("timer_task"):
        test_data["timer_task"].cancel()
    
    current_index = test_data["current_index"]
    questions = test_data["questions"]
    
    if current_index >= len(questions):
        # Тест завершён
        await finish_test(bot, user_id)
        return
    
    question = questions[current_index]
    time_limit = test_data["time_per_question"]
    
    # Формируем текст вопроса
    text = (
        f"❓ <b>Вопрос {current_index + 1} из {len(questions)}</b>\n\n"
        f"{question.text}\n\n"
        f"⏱ Время: {time_limit} секунд"
    )
    
    try:
        await test_data["message"].edit_text(
            text,
            reply_markup=get_test_answers_keyboard(question.answers, question.id),
            parse_mode="HTML"
        )
    except Exception:
        pass
    
    # Запускаем таймер
    test_data["timer_task"] = asyncio.create_task(
        question_timeout(bot, user_id, question.id)
    )


async def question_timeout(bot: Bot, user_id: int, question_id: int):
    """Таймаут вопроса"""
    try:
        if user_id not in active_tests:
            return
        
        test_data = active_tests[user_id]
        time_limit = test_data["time_per_question"]
        
        await asyncio.sleep(time_limit)
    except asyncio.CancelledError:
        # Таймер отменён — пользователь успел ответить
        return
    
    # Проверяем, что вопрос ещё актуален
    if user_id not in active_tests:
        return
    
    current_index = test_data["current_index"]
    questions = test_data["questions"]
    
    if current_index >= len(questions):
        return
    
    current_question = questions[current_index]
    if current_question.id != question_id:
        return
    
    # Время вышло - записываем как неотвеченный
    test_data["answers"].append({
        "question_id": question_id,
        "answer_id": None,
        "is_correct": False,
        "timeout": True
    })
    
    # Переходим к следующему вопросу
    test_data["current_index"] += 1
    
    try:
        await test_data["message"].edit_text(
            f"⏱ <b>Время вышло!</b>\n\n"
            f"Переходим к следующему вопросу...",
            parse_mode="HTML"
        )
        await asyncio.sleep(1.5)
    except Exception:
        pass
    
    await show_question(bot, user_id)


@router.callback_query(F.data.startswith("answer:"), TestStates.in_progress)
async def process_answer(callback: CallbackQuery, state: FSMContext, user=None):
    """Обработка ответа на вопрос"""
    await callback.answer()
    
    user_id = callback.from_user.id
    
    if user_id not in active_tests:
        await callback.message.edit_text(
            "Тест не найден. Пожалуйста, начните заново.",
            reply_markup=get_back_keyboard("tests_back_to_list")
        )
        await state.clear()
        return
    
    test_data = active_tests[user_id]
    
    # Отменяем таймер
    if test_data.get("timer_task"):
        test_data["timer_task"].cancel()
    
    parts = callback.data.split(":")
    question_id = int(parts[1])
    answer_id = int(parts[2])
    
    current_index = test_data["current_index"]
    questions = test_data["questions"]
    
    if current_index >= len(questions):
        return
    
    current_question = questions[current_index]
    
    # Проверяем, что отвечаем на текущий вопрос
    if current_question.id != question_id:
        return
    
    # Проверяем правильность ответа
    is_correct = False
    for answer in current_question.answers:
        if answer.id == answer_id and answer.is_correct:
            is_correct = True
            break
    
    if is_correct:
        test_data["correct_answers"] += 1
    
    test_data["answers"].append({
        "question_id": question_id,
        "answer_id": answer_id,
        "is_correct": is_correct,
        "timeout": False
    })
    
    # Переходим к следующему вопросу
    test_data["current_index"] += 1
    
    # Краткая обратная связь
    feedback = "✅ Верно!" if is_correct else "❌ Неверно"
    
    try:
        await callback.message.edit_text(
            f"{feedback}\n\nСледующий вопрос...",
            parse_mode="HTML"
        )
        await asyncio.sleep(1)
    except Exception:
        pass
    
    await show_question(callback.message.bot, user_id)


async def finish_test(bot: Bot, user_id: int):
    """Завершение теста и подсчёт результатов"""
    if user_id not in active_tests:
        return
    
    test_data = active_tests[user_id]
    
    correct = test_data["correct_answers"]
    total = test_data["total_questions"]
    percent = (correct / total * 100) if total > 0 else 0
    test = test_data["test"]
    passed = percent >= test.passing_score
    
    # Сохраняем результат
    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        
        # Получаем user из БД
        from database.repositories import UserRepository
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(user_id)
        
        if user:
            await test_repo.save_result(
                user_id=user.id,
                test_id=test.id,
                score=correct,
                total_questions=total,
                percent=percent,
                passed=passed,
                branch=user.branch
            )
    
    # Формируем результат
    if passed:
        result_text = (
            f"🎉 <b>Поздравляем!</b>\n\n"
            f"Вы успешно прошли тест «{test.title}»!\n\n"
            f"📊 Ваш результат: {correct} из {total} ({percent:.0f}%)\n"
            f"✅ Проходной балл: {test.passing_score}%\n\n"
            "Отличная работа! Продолжайте в том же духе!"
        )
    else:
        result_text = (
            f"📝 <b>Тест завершён</b>\n\n"
            f"Тест: «{test.title}»\n\n"
            f"📊 Ваш результат: {correct} из {total} ({percent:.0f}%)\n"
            f"❌ Проходной балл: {test.passing_score}%\n\n"
            "К сожалению, тест не пройден. "
            "Рекомендуем повторить обучающие материалы и попробовать снова."
        )
    
    try:
        await test_data["message"].edit_text(
            result_text,
            reply_markup=get_back_keyboard("tests_back_to_list"),
            parse_mode="HTML"
        )
    except Exception:
        pass
    
    # Очищаем данные теста
    del active_tests[user_id]


@router.callback_query(F.data == "tests_back_to_list")
async def back_to_tests_list(callback: CallbackQuery, state: FSMContext, user=None):
    """Вернуться к списку тестов"""
    await callback.answer()
    await state.clear()
    
    # Очищаем активный тест если есть
    user_id = callback.from_user.id
    if user_id in active_tests:
        if active_tests[user_id].get("timer_task"):
            active_tests[user_id]["timer_task"].cancel()
        del active_tests[user_id]
    
    if not user:
        await callback.message.edit_text(
            "Пожалуйста, используйте /start для авторизации."
        )
        return
    
    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        tests = await test_repo.get_tests_by_role(user.role, user.branch)
    
    if not tests:
        await callback.message.edit_text(
            "Для Вашей должности пока нет доступных тестов.",
            reply_markup=get_back_keyboard("back_to_main")
        )
        return
    
    await callback.message.edit_text(
        "📝 <b>Аттестация</b>\n\n"
        "Выберите тест для прохождения:",
        reply_markup=get_tests_keyboard(tests),
        parse_mode="HTML"
    )
