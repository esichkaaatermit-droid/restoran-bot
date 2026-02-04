"""
Скрипт для инициализации тестовых данных в БД
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, async_session_maker
from database.models import (
    User, UserRole, MenuItem, MenuType, MenuItemStatus,
    TrainingMaterial, Test, Question, Answer, MotivationMessage
)
from config import settings


async def create_test_users(session):
    """Создаёт тестовых пользователей"""
    users = [
        User(
            full_name="Иванова Мария Петровна",
            phone="79991234501",
            role=UserRole.HOSTESS,
            branch=settings.DEFAULT_BRANCH
        ),
        User(
            full_name="Петров Алексей Сергеевич",
            phone="79991234502",
            role=UserRole.WAITER,
            branch=settings.DEFAULT_BRANCH
        ),
        User(
            full_name="Сидоров Дмитрий Иванович",
            phone="79991234503",
            role=UserRole.BARTENDER,
            branch=settings.DEFAULT_BRANCH
        ),
        User(
            full_name="Козлова Анна Викторовна",
            phone="79991234504",
            role=UserRole.MANAGER,
            branch=settings.DEFAULT_BRANCH
        ),
    ]
    
    for user in users:
        session.add(user)
    await session.commit()
    print(f"✓ Создано {len(users)} тестовых пользователей")


async def create_menu_items(session):
    """Создаёт тестовые позиции меню"""
    items = [
        # Кухня - Завтраки
        MenuItem(name="Яичница с беконом", description="Классическое блюдо на завтрак",
                 composition="Яйца, бекон, тост, зелень", weight_volume="280г",
                 price=320, category="Завтраки", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Каша овсяная", description="С ягодами и мёдом",
                 composition="Овсянка, молоко, мёд, ягоды", weight_volume="250г",
                 price=180, category="Завтраки", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.GO, branch=settings.DEFAULT_BRANCH),
        
        # Кухня - Салаты
        MenuItem(name="Цезарь с курицей", description="Классический салат",
                 composition="Курица гриль, романо, пармезан, соус цезарь, гренки", weight_volume="250г",
                 price=450, category="Салаты", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Греческий салат", description="Свежие овощи с фетой",
                 composition="Томаты, огурцы, перец, фета, маслины, оливковое масло", weight_volume="220г",
                 price=380, category="Салаты", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        
        # Кухня - Горячие блюда
        MenuItem(name="Стейк Рибай", description="Премиальный стейк",
                 composition="Говядина мраморная, соль, перец, травы", weight_volume="300г",
                 price=1850, category="Горячие блюда", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.STOP, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Паста Карбонара", description="Итальянская классика",
                 composition="Спагетти, бекон, яйцо, пармезан, сливки", weight_volume="320г",
                 price=520, category="Горячие блюда", menu_type=MenuType.KITCHEN,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        
        # Бар - Кофе
        MenuItem(name="Эспрессо", description="Классический итальянский кофе",
                 composition="Кофе арабика", weight_volume="30мл",
                 price=120, category="Кофе", menu_type=MenuType.BAR,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Капучино", description="Кофе с молочной пенкой",
                 composition="Эспрессо, молоко", weight_volume="200мл",
                 price=180, category="Кофе", menu_type=MenuType.BAR,
                 status=MenuItemStatus.GO, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Латте", description="Кофе с большим количеством молока",
                 composition="Эспрессо, молоко", weight_volume="300мл",
                 price=200, category="Кофе", menu_type=MenuType.BAR,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        
        # Бар - Коктейли
        MenuItem(name="Мохито", description="Освежающий коктейль",
                 composition="Ром, мята, лайм, сахар, содовая", weight_volume="300мл",
                 price=420, category="Коктейли", menu_type=MenuType.BAR,
                 status=MenuItemStatus.NORMAL, branch=settings.DEFAULT_BRANCH),
        MenuItem(name="Апероль Шприц", description="Итальянский аперитив",
                 composition="Апероль, просекко, содовая, апельсин", weight_volume="250мл",
                 price=480, category="Коктейли", menu_type=MenuType.BAR,
                 status=MenuItemStatus.GO, branch=settings.DEFAULT_BRANCH),
    ]
    
    for item in items:
        session.add(item)
    await session.commit()
    print(f"✓ Создано {len(items)} позиций меню")


async def create_training_materials(session):
    """Создаёт тестовые обучающие материалы"""
    materials = [
        # Хостес
        TrainingMaterial(
            title="Встреча гостей",
            description="Как правильно встречать гостей ресторана",
            content="""🎯 ВСТРЕЧА ГОСТЕЙ

1. Улыбайтесь и установите зрительный контакт
2. Поприветствуйте гостя: «Добрый день! Добро пожаловать в Бистро ГАВРОШ!»
3. Уточните количество гостей и наличие брони
4. Проводите к столу, идя чуть впереди
5. Предложите меню и сообщите об официанте

Помните: первое впечатление — самое важное!""",
            role=UserRole.HOSTESS,
            order_num=1,
            branch=settings.DEFAULT_BRANCH
        ),
        
        # Официант
        TrainingMaterial(
            title="Стандарты обслуживания",
            description="Основные правила работы официанта",
            content="""📋 СТАНДАРТЫ ОБСЛУЖИВАНИЯ

1. ПРИВЕТСТВИЕ (в течение 1 минуты после посадки)
   - Представьтесь по имени
   - Предложите аперитив

2. ПРИНЯТИЕ ЗАКАЗА
   - Рекомендуйте блюда из Go-листа
   - Уточняйте степень прожарки/аллергии
   - Повторите заказ вслух

3. ПОДАЧА БЛЮД
   - Называйте блюдо при подаче
   - Пожелайте приятного аппетита

4. РАСЧЁТ
   - Принесите счёт в течение 3 минут
   - Поблагодарите и пригласите снова""",
            role=UserRole.WAITER,
            order_num=1,
            branch=settings.DEFAULT_BRANCH
        ),
        
        # Бармен
        TrainingMaterial(
            title="Приготовление кофе",
            description="Техника приготовления кофейных напитков",
            content="""☕ ПРИГОТОВЛЕНИЕ КОФЕ

ЭСПРЕССО:
- Помол: мелкий
- Дозировка: 18г
- Время экстракции: 25-30 сек
- Объём: 30мл

КАПУЧИНО:
- Эспрессо: 30мл
- Молоко: взбить до 65°C
- Пена: 1см, глянцевая
- Подача: сразу после приготовления

ЛАТТЕ:
- Эспрессо: 30мл  
- Молоко: 270мл, взбитое
- Пена: минимальная
- Можно добавить латте-арт""",
            role=UserRole.BARTENDER,
            order_num=1,
            branch=settings.DEFAULT_BRANCH
        ),
        
        # Менеджер
        TrainingMaterial(
            title="Управление сменой",
            description="Организация работы смены",
            content="""👔 УПРАВЛЕНИЕ СМЕНОЙ

ПЕРЕД СМЕНОЙ:
✓ Проверить явку персонала
✓ Провести брифинг (стоп/go-лист, резервы)
✓ Проверить чистоту зала

ВО ВРЕМЯ СМЕНЫ:
✓ Контроль качества обслуживания
✓ Решение конфликтных ситуаций
✓ Координация кухни и зала

ЗАКРЫТИЕ:
✓ Проверить кассу
✓ Провести инвентаризацию бара
✓ Заполнить отчёт смены""",
            role=UserRole.MANAGER,
            order_num=1,
            branch=settings.DEFAULT_BRANCH
        ),
    ]
    
    for material in materials:
        session.add(material)
    await session.commit()
    print(f"✓ Создано {len(materials)} обучающих материалов")


async def create_tests(session):
    """Создаёт тестовые тесты для аттестации"""
    # Тест для официантов
    test1 = Test(
        title="Основы сервиса",
        description="Тест на знание стандартов обслуживания",
        role=UserRole.WAITER,
        passing_score=70,
        max_attempts=3,
        time_per_question=30,
        branch=settings.DEFAULT_BRANCH
    )
    session.add(test1)
    await session.flush()
    
    # Вопросы для теста
    q1 = Question(test_id=test1.id, text="В течение какого времени нужно подойти к гостю после посадки?", order_num=1)
    q2 = Question(test_id=test1.id, text="Что нужно сделать при принятии заказа?", order_num=2)
    q3 = Question(test_id=test1.id, text="В течение какого времени нужно принести счёт?", order_num=3)
    
    session.add_all([q1, q2, q3])
    await session.flush()
    
    # Ответы
    answers = [
        Answer(question_id=q1.id, text="1 минуты", is_correct=True),
        Answer(question_id=q1.id, text="5 минут", is_correct=False),
        Answer(question_id=q1.id, text="10 минут", is_correct=False),
        
        Answer(question_id=q2.id, text="Повторить заказ вслух", is_correct=True),
        Answer(question_id=q2.id, text="Молча записать", is_correct=False),
        Answer(question_id=q2.id, text="Запомнить наизусть", is_correct=False),
        
        Answer(question_id=q3.id, text="3 минут", is_correct=True),
        Answer(question_id=q3.id, text="10 минут", is_correct=False),
        Answer(question_id=q3.id, text="Когда гость попросит", is_correct=False),
    ]
    session.add_all(answers)
    
    # Тест для барменов
    test2 = Test(
        title="Кофейные напитки",
        description="Тест на знание приготовления кофе",
        role=UserRole.BARTENDER,
        passing_score=70,
        max_attempts=3,
        time_per_question=30,
        branch=settings.DEFAULT_BRANCH
    )
    session.add(test2)
    await session.flush()
    
    q4 = Question(test_id=test2.id, text="Какое время экстракции эспрессо?", order_num=1)
    q5 = Question(test_id=test2.id, text="До какой температуры взбивать молоко для капучино?", order_num=2)
    
    session.add_all([q4, q5])
    await session.flush()
    
    answers2 = [
        Answer(question_id=q4.id, text="25-30 секунд", is_correct=True),
        Answer(question_id=q4.id, text="10-15 секунд", is_correct=False),
        Answer(question_id=q4.id, text="45-60 секунд", is_correct=False),
        
        Answer(question_id=q5.id, text="65°C", is_correct=True),
        Answer(question_id=q5.id, text="80°C", is_correct=False),
        Answer(question_id=q5.id, text="50°C", is_correct=False),
    ]
    session.add_all(answers2)
    
    await session.commit()
    print("✓ Создано 2 теста с вопросами")


async def create_motivation_messages(session):
    """Создаёт мотивационные сообщения"""
    messages = [
        "💪 Вы делаете отличную работу! Каждый гость уходит довольным благодаря Вам.",
        "🌟 Ваш профессионализм — это то, что делает наш ресторан особенным!",
        "✨ Помните: улыбка и внимание к деталям — ключ к успеху!",
        "🎯 Сегодня отличный день, чтобы превзойти ожидания гостей!",
        "🏆 Вы — часть лучшей команды! Гордимся Вами!",
        "💫 Каждый день — это возможность стать ещё лучше!",
        "🤝 Вместе мы создаём незабываемый опыт для наших гостей!",
        "⭐ Ваша энергия и позитив заряжают всю команду!",
    ]
    
    for text in messages:
        msg = MotivationMessage(text=text)
        session.add(msg)
    
    await session.commit()
    print(f"✓ Создано {len(messages)} мотивационных сообщений")


async def main():
    """Основная функция"""
    print("=" * 50)
    print("Инициализация тестовых данных")
    print("=" * 50)
    
    # Инициализируем БД
    await init_db()
    print("✓ База данных инициализирована")
    
    async with async_session_maker() as session:
        await create_test_users(session)
        await create_menu_items(session)
        await create_training_materials(session)
        await create_tests(session)
        await create_motivation_messages(session)
    
    print("=" * 50)
    print("Тестовые данные успешно созданы!")
    print("=" * 50)
    print("\nТестовые номера телефонов для привязки:")
    print("  Хостес:   +7 999 123 45 01")
    print("  Официант: +7 999 123 45 02")
    print("  Бармен:   +7 999 123 45 03")
    print("  Менеджер: +7 999 123 45 04")


if __name__ == "__main__":
    asyncio.run(main())
