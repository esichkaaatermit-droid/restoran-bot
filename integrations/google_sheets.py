"""
Интеграция с Google Sheets для синхронизации данных.

Структура таблицы (15 листов):
- Доступ: ФИО, Телефон, Должность, Филиал, Активен
- Завтраки, Основное меню, Сезонное меню, Выпечка и десерты,
  Безалкогольные напитки, Алкогольные напитки:
  Подкатегория, Название блюда, Краткое описание, Состав, Вес/Объём,
  Цена (руб.), Калории, Белки (г), Жиры (г), Углеводы (г)
- Обучение: хостес / Обучение: официанты / Обучение: бармены / Обучение: менеджеры:
  Тема, Название материала, Краткое описание, Текст материала
- Чек-лист: официанты / Чек-лист: менеджеры:
  Категория, Задача
- Аттестация: Название теста, Должность, Проходной балл (%), Количество попыток,
  Секунд на вопрос, Вопрос, Ответ 1-4, Правильный ответ (номер)
- Мотивация: Текст сообщения
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
import aiohttp
import asyncio
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from database.models import MenuType, MenuItemStatus, UserRole

logger = logging.getLogger(__name__)

# Папка для временного хранения файлов
TEMP_FILES_DIR = Path(__file__).parent.parent / "temp_files"
TEMP_FILES_DIR.mkdir(exist_ok=True)

# Маппинг листов меню → (menu_type, category)
MENU_SHEETS = {
    "Завтраки": (MenuType.KITCHEN, "Завтраки"),
    "Основное меню": (MenuType.KITCHEN, "Основное меню"),
    "Сезонное меню": (MenuType.KITCHEN, "Сезонное меню"),
    "Выпечка и десерты": (MenuType.KITCHEN, "Меню выпечки и десертов"),
    "Безалкогольные напитки": (MenuType.BAR, "Безалкогольные напитки"),
    "Алкогольные напитки": (MenuType.BAR, "Алкогольные напитки"),
}

# Маппинг должностей
ROLE_MAP = {
    "хостес": UserRole.HOSTESS,
    "официант": UserRole.WAITER,
    "бармен": UserRole.BARTENDER,
    "менеджер": UserRole.MANAGER,
}

# Маппинг листов обучения → роль
TRAINING_SHEETS = {
    "Обучение: хостес": UserRole.HOSTESS,
    "Обучение: официанты": UserRole.WAITER,
    "Обучение: бармены": UserRole.BARTENDER,
    "Обучение: менеджеры": UserRole.MANAGER,
}

# Маппинг листов чек-листов → роль
CHECKLIST_SHEETS = {
    "Чек-лист: официанты": UserRole.WAITER,
    "Чек-лист: менеджеры": UserRole.MANAGER,
}


class GoogleSheetsSync:
    """Синхронизация данных из Google Sheets в БД"""

    def __init__(self):
        self.spreadsheet = None
    
    @staticmethod
    def convert_drive_url_to_direct(url: str) -> Optional[str]:
        """
        Преобразовать Google Drive ссылку в прямую ссылку для скачивания
        
        Поддерживаемые форматы:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        - Прямые ссылки (возвращаются как есть)
        """
        if not url:
            return None
        
        # Проверяем, что это Google Drive ссылка
        if "drive.google.com" not in url:
            # Если это уже прямая ссылка - возвращаем как есть
            return url
        
        # Извлекаем file_id из разных форматов Google Drive ссылок
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',  # /file/d/FILE_ID/view
            r'id=([a-zA-Z0-9_-]+)',       # ?id=FILE_ID
            r'/d/([a-zA-Z0-9_-]+)',       # /d/FILE_ID
        ]
        
        file_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                break
        
        if not file_id:
            logger.warning(f"Не удалось извлечь file_id из ссылки: {url}")
            return None
        
        # Формируем прямую ссылку для скачивания
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        return direct_url
    
    @staticmethod
    async def download_file(url: str, destination: Path) -> bool:
        """
        Скачать файл по ссылке
        
        Args:
            url: URL файла
            destination: Путь для сохранения
        
        Returns:
            True если успешно, False иначе
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания файла: HTTP {response.status}")
                        return False
                    
                    # Сохраняем файл
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with open(destination, 'wb') as f:
                        f.write(await response.read())
                    
                    logger.info(f"Файл скачан: {destination}")
                    return True
        except Exception as e:
            logger.error(f"Ошибка скачивания файла {url}: {e}")
            return False

    def connect(self) -> bool:
        """Подключиться к Google Sheets"""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
            ]
            credentials = Credentials.from_service_account_file(
                settings.GOOGLE_CREDENTIALS_FILE,
                scopes=scopes,
            )
            client = gspread.authorize(credentials)
            self.spreadsheet = client.open_by_key(settings.GOOGLE_SHEETS_ID)
            logger.info("Успешное подключение к Google Sheets")
            return True
        except FileNotFoundError:
            logger.error(f"Файл credentials не найден: {settings.GOOGLE_CREDENTIALS_FILE}")
            return False
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            return False

    def _find_worksheet(self, sheet_name: str):
        """Найти лист по имени (с учётом пробелов)"""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            for ws in self.spreadsheet.worksheets():
                if ws.title.strip() == sheet_name.strip():
                    logger.info(f"Лист найден с пробелами: '{ws.title}' -> '{sheet_name}'")
                    return ws
            return None

    def _get_sheet_records(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Получить записи из листа"""
        try:
            worksheet = self._find_worksheet(sheet_name)
            if not worksheet:
                logger.warning(f"Лист '{sheet_name}' не найден в таблице")
                return []
            try:
                records = worksheet.get_all_records()
                return records
            except Exception:
                # Если заголовки неуникальны — читаем вручную
                all_values = worksheet.get_all_values()
                if len(all_values) < 2:
                    return []
                headers = all_values[0]
                # Делаем заголовки уникальными
                seen = {}
                unique_headers = []
                for h in headers:
                    h = h.strip()
                    if h in seen:
                        seen[h] += 1
                        unique_headers.append(f"{h}_{seen[h]}")
                    else:
                        seen[h] = 0
                        unique_headers.append(h)
                records = []
                for row in all_values[1:]:
                    record = {}
                    for i, val in enumerate(row):
                        if i < len(unique_headers):
                            record[unique_headers[i]] = val
                    records.append(record)
                return records
        except Exception as e:
            logger.error(f"Ошибка чтения листа '{sheet_name}': {e}")
            return []

    async def _async_get_sheet_records(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Асинхронная обёртка для _get_sheet_records (не блокирует event loop)"""
        return await asyncio.to_thread(self._get_sheet_records, sheet_name)

    async def _async_connect(self) -> bool:
        """Асинхронная обёртка для connect (не блокирует event loop)"""
        return await asyncio.to_thread(self.connect)

    def _safe_float(self, value: Any) -> Optional[float]:
        """Безопасное преобразование в float"""
        if value is None or value == "":
            return None
        try:
            return float(str(value).replace(",", ".").strip())
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Безопасное преобразование в int"""
        if value is None or value == "":
            return None
        try:
            return int(float(str(value).replace(",", ".").strip()))
        except (ValueError, TypeError):
            return None

    # ========== СОТРУДНИКИ ==========

    @staticmethod
    def _is_phone(value: str) -> bool:
        """Проверить, похоже ли значение на номер телефона"""
        digits = ''.join(filter(str.isdigit, value))
        return len(digits) >= 7

    @staticmethod
    def _normalize_username(value: str) -> str:
        """Нормализовать Telegram username (без @, в нижнем регистре)"""
        return value.lstrip("@").strip().lower()

    def read_employees(self) -> List[Dict[str, Any]]:
        """Прочитать сотрудников из Google Sheets (лист 'Доступ').

        Колонка 'Телефон' может содержать:
        - Номер телефона (79991234567, +7 999 123-45-67, 89991234567)
        - Telegram username (@username или username)
        """
        records = self._get_sheet_records("Доступ")
        employees = []

        for row in records:
            full_name = str(row.get("ФИО", "")).strip()
            contact = str(row.get("Телефон", "")).strip()
            role_str = str(row.get("Должность", "")).strip().lower()
            branch = str(row.get("Филиал", "")).strip()
            active_str = str(row.get("Активен", "да")).strip().lower()

            if not full_name or not contact:
                continue

            role = ROLE_MAP.get(role_str)
            if not role:
                logger.warning(f"Неизвестная должность '{role_str}' для {full_name}")
                continue

            if not branch:
                branch = settings.DEFAULT_BRANCH

            # Определяем: телефон или username
            phone = None
            telegram_username = None

            if self._is_phone(contact):
                phone = contact
            else:
                telegram_username = self._normalize_username(contact)

            employees.append({
                "full_name": full_name,
                "phone": phone,
                "telegram_username": telegram_username,
                "role": role,
                "branch": branch,
                "is_active": active_str in ("да", "yes", "true", "1", "активен"),
            })

        logger.info(f"Прочитано {len(employees)} сотрудников из Google Sheets")
        return employees

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Нормализация номера телефона для сравнения (как в UserRepository)"""
        digits = "".join(filter(str.isdigit, phone))
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        if len(digits) == 10:
            digits = "7" + digits
        return digits

    def find_employee_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Найти сотрудника по телефону в таблице "Доступ".
        Возвращает dict с данными сотрудника или None если не найден.
        """
        if not self.connect():
            return None

        normalized_input = self._normalize_phone(phone)
        if len(normalized_input) < 10:
            return None

        employees = self.read_employees()
        for emp in employees:
            if not emp.get("phone"):
                continue
            normalized_emp = self._normalize_phone(emp["phone"])
            if normalized_emp == normalized_input and emp.get("is_active", True):
                return emp

        return None

    # ========== МЕНЮ ==========

    def read_menu(self) -> List[Dict[str, Any]]:
        """Прочитать все позиции меню из Google Sheets"""
        all_items = []

        for sheet_name, (menu_type, category) in MENU_SHEETS.items():
            records = self._get_sheet_records(sheet_name)

            for row in records:
                name = str(row.get("Название блюда", "")).strip()
                if not name:
                    continue

                price = self._safe_float(row.get("Цена (руб.)"))
                if price is None:
                    logger.warning(f"Нет цены для '{name}' в листе '{sheet_name}'")
                    continue

                item = {
                    "name": name,
                    "description": str(row.get("Краткое описание", "")).strip() or None,
                    "composition": str(row.get("Состав", "")).strip() or None,
                    "weight_volume": str(row.get("Вес/Объём", "")).strip() or None,
                    "price": price,
                    "category": category,
                    "subcategory": str(row.get("Подкатегория", "")).strip() or None,
                    "menu_type": menu_type,
                    "status": MenuItemStatus.NORMAL,
                    "branch": settings.DEFAULT_BRANCH,
                    "calories": self._safe_int(row.get("Калории")),
                    "proteins": self._safe_float(row.get("Белки (г)")),
                    "fats": self._safe_float(row.get("Жиры (г)")),
                    "carbs": self._safe_float(row.get("Углеводы (г)")),
                }
                all_items.append(item)

        logger.info(f"Прочитано {len(all_items)} позиций меню из Google Sheets")
        return all_items

    # ========== ОБУЧЕНИЕ ==========

    def read_training(self) -> List[Dict[str, Any]]:
        """
        Прочитать обучающие материалы из Google Sheets.
        Отдельный лист для каждой роли:
        - Обучение хостес
        - Обучение официанты
        - Обучение бармены
        - Обучение менеджеры
        
        Поддерживает столбец "Ссылка на файл" для автоматической загрузки PDF из Google Drive
        """
        materials = []
        order_counter = {}

        for sheet_name, role in TRAINING_SHEETS.items():
            records = self._get_sheet_records(sheet_name)

            role_key = role.value
            order_counter[role_key] = 0

            for row in records:
                title = str(row.get("Название материала", "")).strip()
                content = str(row.get("Текст материала", "")).strip()

                if not title or not content:
                    continue

                order_counter[role_key] += 1

                # Получаем ссылку на файл (Google Drive или прямая ссылка)
                # Поддерживаем оба варианта названия колонки
                file_url = str(row.get("Файл PDF", "") or row.get("Ссылка на файл", "")).strip() or None
                
                materials.append({
                    "title": title,
                    "description": str(row.get("Краткое описание", "")).strip() or None,
                    "content": content,
                    "category": str(row.get("Тема", "")).strip() or None,
                    "role": role,
                    "order_num": order_counter[role_key],
                    "branch": settings.DEFAULT_BRANCH,
                    "file_url": file_url,  # Новое поле
                })

        logger.info(f"Прочитано {len(materials)} обучающих материалов из Google Sheets")
        return materials

    # ========== ЧЕК-ЛИСТЫ ==========

    def read_checklists(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Прочитать чек-листы из Google Sheets.
        Листы: Чек-лист официанты, Чек-лист менеджеры.

        Возвращает: {role_value: [{category, task, order_num, role}]}
        """
        checklists = {}

        for sheet_name, role in CHECKLIST_SHEETS.items():
            records = self._get_sheet_records(sheet_name)
            items = []
            order = 0

            for row in records:
                task = str(row.get("Задача", "")).strip()
                if not task:
                    continue

                order += 1
                items.append({
                    "category": str(row.get("Категория", "")).strip() or None,
                    "task": task,
                    "order_num": order,
                    "role": role,
                })

            checklists[role.value] = items
            logger.info(f"Прочитано {len(items)} задач из '{sheet_name}'")

        return checklists

    # ========== ТЕСТЫ ==========

    def read_tests(self) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Прочитать тесты из Google Sheets.

        Возвращает:
        - tests: список тестов [{title, role, passing_score, ...}]
        - questions: {test_title: [{text, answers: [{text, is_correct}]}]}
        """
        records = self._get_sheet_records("Аттестация")
        tests_map = {}  # title+role → test info
        questions_map = {}  # title+role → [questions]

        for row in records:
            test_title = str(row.get("Название теста", "")).strip()
            role_str = str(row.get("Должность", "")).strip().lower()
            question_text = str(row.get("Вопрос", "")).strip()

            if not test_title or not question_text:
                continue

            role = ROLE_MAP.get(role_str)
            if not role:
                continue

            key = f"{test_title}|{role_str}"

            # Сохраняем информацию о тесте (из первой строки)
            if key not in tests_map:
                tests_map[key] = {
                    "title": test_title,
                    "role": role,
                    "passing_score": self._safe_int(row.get("Проходной балл (%)")) or 70,
                    "max_attempts": self._safe_int(row.get("Количество попыток")) or 3,
                    "time_per_question": self._safe_int(row.get("Секунд на вопрос")) or 30,
                    "branch": settings.DEFAULT_BRANCH,
                }
                questions_map[key] = []

            # Собираем ответы
            answers = []
            correct_num = self._safe_int(row.get("Правильный ответ (номер)"))

            for i in range(1, 5):
                answer_text = str(row.get(f"Ответ {i}", "")).strip()
                if answer_text:
                    answers.append({
                        "text": answer_text,
                        "is_correct": i == correct_num,
                    })

            if answers:
                questions_map[key].append({
                    "text": question_text,
                    "order_num": len(questions_map[key]) + 1,
                    "answers": answers,
                })

        tests = list(tests_map.values())
        logger.info(
            f"Прочитано {len(tests)} тестов, "
            f"{sum(len(q) for q in questions_map.values())} вопросов из Google Sheets"
        )
        return tests, questions_map

    # ========== МОТИВАЦИЯ ==========

    def read_motivation(self) -> List[str]:
        """Прочитать мотивационные сообщения из Google Sheets"""
        records = self._get_sheet_records("Мотивация")
        messages = []

        for row in records:
            text = str(row.get("Текст сообщения", "")).strip()
            if text:
                messages.append(text)

        logger.info(f"Прочитано {len(messages)} мотивационных сообщений из Google Sheets")
        return messages

    # ========== ПОЛНАЯ СИНХРОНИЗАЦИЯ ==========

    async def sync_all(self) -> Dict[str, Any]:
        """
        Выполнить полную синхронизацию всех данных.
        Возвращает отчёт о синхронизации.
        """
        from database.database import async_session_maker
        from database.repositories import (
            UserRepository,
            MenuRepository,
            TrainingRepository,
            TestRepository,
            MotivationRepository,
            ChecklistRepository,
        )

        if not await self._async_connect():
            return {"success": False, "error": "Не удалось подключиться к Google Sheets"}

        report = {"success": True, "details": {}}
        branch = settings.DEFAULT_BRANCH

        # 1. Синхронизация сотрудников
        try:
            async with async_session_maker() as session:
                employees = await asyncio.to_thread(self.read_employees)
                user_repo = UserRepository(session)
                created, updated, deactivated = 0, 0, 0

                for emp in employees:
                    # Ищем существующего сотрудника по телефону или username
                    existing = None
                    if emp["phone"]:
                        existing = await user_repo.get_by_phone_any(emp["phone"])
                    if not existing and emp.get("telegram_username"):
                        existing = await user_repo.get_by_username(emp["telegram_username"])

                    if existing:
                        update_data = {
                            "full_name": emp["full_name"],
                            "role": emp["role"],
                            "branch": emp["branch"],
                            "is_active": emp["is_active"],
                        }
                        if emp["phone"]:
                            update_data["phone"] = emp["phone"]
                        if emp.get("telegram_username"):
                            update_data["telegram_username"] = emp["telegram_username"]
                        await user_repo.update(existing.id, **update_data)
                        if emp["is_active"]:
                            updated += 1
                        else:
                            deactivated += 1
                    else:
                        await user_repo.create(
                            full_name=emp["full_name"],
                            phone=emp.get("phone"),
                            role=emp["role"],
                            branch=emp["branch"],
                            telegram_username=emp.get("telegram_username"),
                        )
                        created += 1

                report["details"]["employees"] = {
                    "created": created,
                    "updated": updated,
                    "deactivated": deactivated,
                }
        except Exception as e:
            logger.error(f"Ошибка синхронизации сотрудников: {e}")
            report["details"]["employees"] = {"error": str(e)}

        # 2. Синхронизация меню (атомарная транзакция)
        try:
            async with async_session_maker() as session:
                menu_items = await asyncio.to_thread(self.read_menu)
                menu_repo = MenuRepository(session)

                existing_items = await menu_repo.get_all(branch=branch)
                status_map = {}
                photo_map = {}
                for item in existing_items:
                    status_map[item.name.lower()] = item.status
                    if item.photo:
                        photo_map[item.name.lower()] = item.photo

                await menu_repo.delete_all_by_branch(branch, commit=False)

                for item_data in menu_items:
                    name_lower = item_data["name"].lower()
                    if name_lower in status_map:
                        item_data["status"] = status_map[name_lower]
                    if name_lower in photo_map:
                        item_data["photo"] = photo_map[name_lower]

                count = await menu_repo.bulk_create(menu_items, commit=False)
                await session.commit()
                report["details"]["menu"] = {"count": count}
        except Exception as e:
            logger.error(f"Ошибка синхронизации меню: {e}")
            report["details"]["menu"] = {"error": str(e)}

        # 3. Синхронизация обучения
        try:
            async with async_session_maker() as session:
                materials = await asyncio.to_thread(self.read_training)
                training_repo = TrainingRepository(session)

                existing_materials = await training_repo.get_all(branch=branch)
                file_map = {}
                for mat in existing_materials:
                    if mat.file_path:
                        file_map[mat.title.lower()] = mat.file_path

                await training_repo.delete_all_by_branch(branch, commit=False)

                # Обрабатываем ссылки на файлы
                files_downloaded = 0
                for mat_data in materials:
                    title_lower = mat_data["title"].lower()
                    
                    # Если есть ссылка на файл - скачиваем
                    if mat_data.get("file_url"):
                        direct_url = self.convert_drive_url_to_direct(mat_data["file_url"])
                        if direct_url:
                            # Создаем путь для сохранения
                            safe_title = "".join(c for c in mat_data["title"] if c.isalnum() or c in (' ', '_')).rstrip()
                            file_path = TEMP_FILES_DIR / f"{safe_title}.pdf"
                            
                            # Скачиваем файл
                            if await self.download_file(direct_url, file_path):
                                mat_data["file_path"] = str(file_path)
                                files_downloaded += 1
                            else:
                                # Если не удалось скачать, пытаемся использовать старый файл
                                if title_lower in file_map:
                                    mat_data["file_path"] = file_map[title_lower]
                        else:
                            # Если не удалось преобразовать ссылку, используем старый файл
                            if title_lower in file_map:
                                mat_data["file_path"] = file_map[title_lower]
                    else:
                        # Если нет ссылки, сохраняем старый файл если был
                        if title_lower in file_map:
                            mat_data["file_path"] = file_map[title_lower]
                    
                    # Удаляем временное поле
                    mat_data.pop("file_url", None)

                count = await training_repo.bulk_create(materials, commit=False)
                await session.commit()
                report["details"]["training"] = {
                    "count": count,
                    "files_downloaded": files_downloaded
                }
        except Exception as e:
            logger.error(f"Ошибка синхронизации обучения: {e}")
            report["details"]["training"] = {"error": str(e)}

        # 4. Синхронизация тестов
        try:
            async with async_session_maker() as session:
                tests, questions_map = await asyncio.to_thread(self.read_tests)
                test_repo = TestRepository(session)

                await test_repo.delete_all_by_branch(branch, commit=False)

                test_count = 0
                question_count = 0

                for test_data in tests:
                    role_str = None
                    for r_str, r_enum in ROLE_MAP.items():
                        if r_enum == test_data["role"]:
                            role_str = r_str
                            break
                    map_key = f"{test_data['title']}|{role_str}"

                    test = await test_repo.create_test(
                        commit=False,
                        title=test_data["title"],
                        role=test_data["role"],
                        passing_score=test_data["passing_score"],
                        max_attempts=test_data["max_attempts"],
                        time_per_question=test_data["time_per_question"],
                        branch=test_data["branch"],
                    )
                    test_count += 1

                    questions = questions_map.get(map_key, [])
                    for q_data in questions:
                        question = await test_repo.add_question(
                            test_id=test.id,
                            text=q_data["text"],
                            order_num=q_data["order_num"],
                            commit=False,
                        )
                        question_count += 1

                        for a_data in q_data["answers"]:
                            await test_repo.add_answer(
                                question_id=question.id,
                                text=a_data["text"],
                                is_correct=a_data["is_correct"],
                                commit=False,
                            )

                await session.commit()
                report["details"]["tests"] = {
                    "tests": test_count,
                    "questions": question_count,
                }
        except Exception as e:
            logger.error(f"Ошибка синхронизации тестов: {e}")
            report["details"]["tests"] = {"error": str(e)}

        # 5. Синхронизация чек-листов
        try:
            async with async_session_maker() as session:
                checklists = await asyncio.to_thread(self.read_checklists)
                checklist_repo = ChecklistRepository(session)

                await checklist_repo.delete_all_by_branch(branch, commit=False)

                total_items = 0
                for role_value, items in checklists.items():
                    for item in items:
                        item["branch"] = branch
                    count = await checklist_repo.bulk_create(items, commit=False)
                    total_items += count

                await session.commit()
                report["details"]["checklists"] = {"count": total_items}
        except Exception as e:
            logger.error(f"Ошибка синхронизации чек-листов: {e}")
            report["details"]["checklists"] = {"error": str(e)}

        # 6. Синхронизация мотивации
        try:
            async with async_session_maker() as session:
                messages = await asyncio.to_thread(self.read_motivation)
                motivation_repo = MotivationRepository(session)

                await motivation_repo.delete_all(commit=False)
                count = await motivation_repo.bulk_create(messages, commit=False)
                await session.commit()
                report["details"]["motivation"] = {"count": count}
        except Exception as e:
            logger.error(f"Ошибка синхронизации мотивации: {e}")
            report["details"]["motivation"] = {"error": str(e)}

        return report
