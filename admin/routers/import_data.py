import io
from typing import List, Dict, Any

from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

from database.database import async_session_maker
from database.repositories import MenuRepository, TrainingRepository, TestRepository, MotivationRepository
from database.models import MenuType, MenuItemStatus, UserRole
from config import settings
from admin.auth import get_current_user

router = APIRouter(prefix="/import", tags=["import"])
templates = Jinja2Templates(directory="admin/templates")


@router.get("/", response_class=HTMLResponse)
async def import_page(request: Request, user=Depends(get_current_user)):
    """Страница импорта данных"""
    return templates.TemplateResponse(
        "import/index.html",
        {
            "request": request,
            "default_branch": settings.DEFAULT_BRANCH,
        }
    )


@router.post("/menu")
async def import_menu(
    request: Request,
    file: UploadFile = File(...),
    branch: str = Form(...),
    replace_existing: bool = Form(False),
    user=Depends(get_current_user)
):
    """Импорт меню из Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel (.xlsx или .xls)")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Ожидаемые колонки: name, description, composition, weight_volume, price, category, menu_type, status
        required_columns = ['name', 'price', 'category', 'menu_type']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Отсутствует обязательная колонка: {col}"
                )
        
        items = []
        for _, row in df.iterrows():
            menu_type_str = str(row['menu_type']).lower().strip()
            if menu_type_str in ['кухня', 'kitchen', 'к']:
                menu_type = MenuType.KITCHEN
            elif menu_type_str in ['бар', 'bar', 'б']:
                menu_type = MenuType.BAR
            else:
                continue  # Пропускаем некорректные записи
            
            status = MenuItemStatus.NORMAL
            if 'status' in df.columns and pd.notna(row.get('status')):
                status_str = str(row['status']).lower().strip()
                if status_str in ['stop', 'стоп', 'с']:
                    status = MenuItemStatus.STOP
                elif status_str in ['go', 'го', 'г']:
                    status = MenuItemStatus.GO
            
            item = {
                'name': str(row['name']).strip(),
                'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                'composition': str(row.get('composition', '')).strip() if pd.notna(row.get('composition')) else None,
                'weight_volume': str(row.get('weight_volume', '')).strip() if pd.notna(row.get('weight_volume')) else None,
                'price': float(row['price']),
                'category': str(row['category']).strip(),
                'menu_type': menu_type,
                'status': status,
                'branch': branch,
            }
            items.append(item)
        
        async with async_session_maker() as session:
            menu_repo = MenuRepository(session)
            
            if replace_existing:
                await menu_repo.delete_all_by_branch(branch)
            
            count = await menu_repo.bulk_create(items)
        
        return templates.TemplateResponse(
            "import/success.html",
            {
                "request": request,
                "message": f"Успешно импортировано {count} позиций меню",
                "back_url": "/import/"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/training")
async def import_training(
    request: Request,
    file: UploadFile = File(...),
    branch: str = Form(...),
    replace_existing: bool = Form(False),
    user=Depends(get_current_user)
):
    """Импорт обучающих материалов из Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Ожидаемые колонки: title, description, content, role, order_num
        required_columns = ['title', 'content', 'role']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Отсутствует обязательная колонка: {col}"
                )
        
        materials = []
        for _, row in df.iterrows():
            role_str = str(row['role']).lower().strip()
            role_map = {
                'хостес': UserRole.HOSTESS,
                'hostess': UserRole.HOSTESS,
                'официант': UserRole.WAITER,
                'waiter': UserRole.WAITER,
                'бармен': UserRole.BARTENDER,
                'bartender': UserRole.BARTENDER,
                'менеджер': UserRole.MANAGER,
                'manager': UserRole.MANAGER,
            }
            
            if role_str not in role_map:
                continue
            
            material = {
                'title': str(row['title']).strip(),
                'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                'content': str(row['content']).strip(),
                'role': role_map[role_str],
                'order_num': int(row.get('order_num', 0)) if pd.notna(row.get('order_num')) else 0,
                'branch': branch,
            }
            materials.append(material)
        
        async with async_session_maker() as session:
            training_repo = TrainingRepository(session)
            
            if replace_existing:
                await training_repo.delete_all_by_branch(branch)
            
            count = await training_repo.bulk_create(materials)
        
        return templates.TemplateResponse(
            "import/success.html",
            {
                "request": request,
                "message": f"Успешно импортировано {count} обучающих материалов",
                "back_url": "/import/"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/tests")
async def import_tests(
    request: Request,
    file: UploadFile = File(...),
    branch: str = Form(...),
    replace_existing: bool = Form(False),
    user=Depends(get_current_user)
):
    """Импорт тестов из Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    try:
        contents = await file.read()
        
        # Читаем листы: tests, questions, answers
        excel_file = pd.ExcelFile(io.BytesIO(contents))
        
        if 'tests' not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="Отсутствует лист 'tests'")
        
        tests_df = pd.read_excel(excel_file, sheet_name='tests')
        questions_df = pd.read_excel(excel_file, sheet_name='questions') if 'questions' in excel_file.sheet_names else None
        answers_df = pd.read_excel(excel_file, sheet_name='answers') if 'answers' in excel_file.sheet_names else None
        
        role_map = {
            'хостес': UserRole.HOSTESS,
            'hostess': UserRole.HOSTESS,
            'официант': UserRole.WAITER,
            'waiter': UserRole.WAITER,
            'бармен': UserRole.BARTENDER,
            'bartender': UserRole.BARTENDER,
            'менеджер': UserRole.MANAGER,
            'manager': UserRole.MANAGER,
        }
        
        async with async_session_maker() as session:
            test_repo = TestRepository(session)
            
            if replace_existing:
                await test_repo.delete_all_by_branch(branch)
            
            test_count = 0
            test_id_map = {}  # excel_id -> db_id
            
            for _, row in tests_df.iterrows():
                role_str = str(row['role']).lower().strip()
                if role_str not in role_map:
                    continue
                
                test = await test_repo.create_test(
                    title=str(row['title']).strip(),
                    description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                    role=role_map[role_str],
                    passing_score=int(row.get('passing_score', 70)) if pd.notna(row.get('passing_score')) else 70,
                    max_attempts=int(row.get('max_attempts', 3)) if pd.notna(row.get('max_attempts')) else 3,
                    time_per_question=int(row.get('time_per_question', 30)) if pd.notna(row.get('time_per_question')) else 30,
                    branch=branch,
                )
                test_id_map[row.get('id', test_count)] = test.id
                test_count += 1
            
            question_id_map = {}  # excel_id -> db_id
            
            if questions_df is not None:
                for _, row in questions_df.iterrows():
                    test_excel_id = row.get('test_id')
                    if test_excel_id not in test_id_map:
                        continue
                    
                    question = await test_repo.add_question(
                        test_id=test_id_map[test_excel_id],
                        text=str(row['text']).strip(),
                        order_num=int(row.get('order_num', 0)) if pd.notna(row.get('order_num')) else 0
                    )
                    question_id_map[row.get('id')] = question.id
            
            if answers_df is not None:
                for _, row in answers_df.iterrows():
                    question_excel_id = row.get('question_id')
                    if question_excel_id not in question_id_map:
                        continue
                    
                    is_correct = False
                    if pd.notna(row.get('is_correct')):
                        is_correct_val = row['is_correct']
                        if isinstance(is_correct_val, bool):
                            is_correct = is_correct_val
                        elif isinstance(is_correct_val, (int, float)):
                            is_correct = bool(is_correct_val)
                        elif isinstance(is_correct_val, str):
                            is_correct = is_correct_val.lower() in ['true', '1', 'да', 'yes']
                    
                    await test_repo.add_answer(
                        question_id=question_id_map[question_excel_id],
                        text=str(row['text']).strip(),
                        is_correct=is_correct
                    )
        
        return templates.TemplateResponse(
            "import/success.html",
            {
                "request": request,
                "message": f"Успешно импортировано {test_count} тестов",
                "back_url": "/import/"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/stopgo")
async def import_stop_go(
    request: Request,
    file: UploadFile = File(...),
    branch: str = Form(...),
    user=Depends(get_current_user)
):
    """Импорт стоп/go-листа из Excel (обновление статусов)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Ожидаемые колонки: name, status (stop/go/normal)
        if 'name' not in df.columns or 'status' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Файл должен содержать колонки: name, status"
            )
        
        async with async_session_maker() as session:
            menu_repo = MenuRepository(session)
            all_items = await menu_repo.get_all(branch=branch)
            
            # Создаём словарь для быстрого поиска по имени
            items_by_name = {item.name.lower(): item for item in all_items}
            
            updated = 0
            for _, row in df.iterrows():
                name = str(row['name']).lower().strip()
                status_str = str(row['status']).lower().strip()
                
                if name in items_by_name:
                    item = items_by_name[name]
                    
                    if status_str in ['stop', 'стоп', 'с']:
                        new_status = MenuItemStatus.STOP
                    elif status_str in ['go', 'го', 'г']:
                        new_status = MenuItemStatus.GO
                    else:
                        new_status = MenuItemStatus.NORMAL
                    
                    await menu_repo.update_status(item.id, new_status)
                    updated += 1
        
        return templates.TemplateResponse(
            "import/success.html",
            {
                "request": request,
                "message": f"Обновлено {updated} позиций",
                "back_url": "/import/"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/motivation")
async def import_motivation(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Импорт мотивационных сообщений из Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        if 'text' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Файл должен содержать колонку: text"
            )
        
        texts = [str(row['text']).strip() for _, row in df.iterrows() if pd.notna(row.get('text'))]
        
        async with async_session_maker() as session:
            motivation_repo = MotivationRepository(session)
            count = await motivation_repo.bulk_create(texts)
        
        return templates.TemplateResponse(
            "import/success.html",
            {
                "request": request,
                "message": f"Добавлено {count} мотивационных сообщений",
                "back_url": "/import/"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке файла: {str(e)}")
