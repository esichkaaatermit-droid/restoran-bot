"""
Скрипт для создания Excel-шаблонов для импорта данных
"""
import pandas as pd
from pathlib import Path


def create_menu_template():
    """Создаёт шаблон для меню"""
    data = {
        'name': ['Цезарь с курицей', 'Борщ украинский', 'Американо', 'Мохито'],
        'description': ['Классический салат с курицей гриль', 'Традиционный борщ со сметаной', 'Классический кофе', 'Освежающий коктейль'],
        'composition': ['Курица, салат романо, пармезан, соус цезарь, гренки', 'Свекла, капуста, картофель, морковь, говядина, сметана', 'Эспрессо, вода', 'Ром, мята, лайм, сахар, содовая'],
        'weight_volume': ['250г', '350мл', '200мл', '300мл'],
        'price': [450, 280, 150, 420],
        'category': ['Салаты', 'Первые блюда', 'Кофе', 'Коктейли'],
        'menu_type': ['кухня', 'кухня', 'бар', 'бар'],
        'status': ['normal', 'normal', 'go', 'normal']
    }
    return pd.DataFrame(data)


def create_training_template():
    """Создаёт шаблон для обучающих материалов"""
    data = {
        'title': [
            'Стандарты сервиса',
            'Работа с гостями',
            'Приготовление кофе',
            'Управление сменой'
        ],
        'description': [
            'Основные правила обслуживания гостей',
            'Как правильно встречать и провожать гостей',
            'Техника приготовления кофейных напитков',
            'Организация работы смены'
        ],
        'content': [
            'Полный текст материала по стандартам сервиса...',
            'Полный текст материала по работе с гостями...',
            'Полный текст материала по приготовлению кофе...',
            'Полный текст материала по управлению сменой...'
        ],
        'role': ['официант', 'хостес', 'бармен', 'менеджер'],
        'order_num': [1, 1, 1, 1]
    }
    return pd.DataFrame(data)


def create_tests_template():
    """Создаёт шаблон для тестов (3 листа)"""
    tests = pd.DataFrame({
        'id': [1, 2],
        'title': ['Тест по меню кухни', 'Тест по напиткам'],
        'description': ['Проверка знаний меню кухни', 'Проверка знаний барного меню'],
        'role': ['официант', 'бармен'],
        'passing_score': [70, 70],
        'max_attempts': [3, 3],
        'time_per_question': [30, 30]
    })
    
    questions = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'test_id': [1, 1, 2, 2],
        'text': [
            'Какой соус используется в салате Цезарь?',
            'Какова граммовка борща?',
            'Сколько мл в стандартном американо?',
            'Какой основной ингредиент в мохито?'
        ],
        'order_num': [1, 2, 1, 2]
    })
    
    answers = pd.DataFrame({
        'question_id': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
        'text': [
            'Соус Цезарь', 'Майонез', 'Кетчуп',
            '350мл', '250мл', '400мл',
            '200мл', '150мл', '300мл',
            'Ром', 'Водка', 'Джин'
        ],
        'is_correct': [
            True, False, False,
            True, False, False,
            True, False, False,
            True, False, False
        ]
    })
    
    return tests, questions, answers


def create_stopgo_template():
    """Создаёт шаблон для стоп/go листа"""
    data = {
        'name': ['Цезарь с курицей', 'Борщ украинский', 'Американо'],
        'status': ['stop', 'normal', 'go']
    }
    return pd.DataFrame(data)


def create_motivation_template():
    """Создаёт шаблон для мотивационных сообщений"""
    data = {
        'text': [
            'Вы делаете отличную работу! Каждый гость уходит довольным благодаря Вам.',
            'Ваш профессионализм — это то, что делает наш ресторан особенным!',
            'Помните: улыбка и внимание к деталям — ключ к успеху!',
            'Сегодня отличный день, чтобы превзойти ожидания гостей!',
            'Вы — часть лучшей команды! Гордимся Вами!'
        ]
    }
    return pd.DataFrame(data)


def main():
    """Создаёт все шаблоны"""
    output_dir = Path('excel_templates')
    output_dir.mkdir(exist_ok=True)
    
    # Меню
    menu_df = create_menu_template()
    menu_df.to_excel(output_dir / 'menu_template.xlsx', index=False)
    print('✓ Создан шаблон меню: menu_template.xlsx')
    
    # Обучение
    training_df = create_training_template()
    training_df.to_excel(output_dir / 'training_template.xlsx', index=False)
    print('✓ Создан шаблон обучения: training_template.xlsx')
    
    # Тесты
    tests_df, questions_df, answers_df = create_tests_template()
    with pd.ExcelWriter(output_dir / 'tests_template.xlsx') as writer:
        tests_df.to_excel(writer, sheet_name='tests', index=False)
        questions_df.to_excel(writer, sheet_name='questions', index=False)
        answers_df.to_excel(writer, sheet_name='answers', index=False)
    print('✓ Создан шаблон тестов: tests_template.xlsx')
    
    # Стоп/Go лист
    stopgo_df = create_stopgo_template()
    stopgo_df.to_excel(output_dir / 'stopgo_template.xlsx', index=False)
    print('✓ Создан шаблон стоп/go листа: stopgo_template.xlsx')
    
    # Мотивация
    motivation_df = create_motivation_template()
    motivation_df.to_excel(output_dir / 'motivation_template.xlsx', index=False)
    print('✓ Создан шаблон мотивации: motivation_template.xlsx')
    
    print(f'\nВсе шаблоны сохранены в папку: {output_dir.absolute()}')


if __name__ == '__main__':
    main()
