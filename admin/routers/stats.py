from typing import Optional
from datetime import datetime, date

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database.database import async_session_maker
from database.repositories import TestRepository
from database.models import UserRole
from config import settings
from admin.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])
templates = Jinja2Templates(directory="admin/templates")


@router.get("/", response_class=HTMLResponse)
async def stats_page(
    request: Request,
    role: Optional[str] = None,
    test_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Страница статистики тестов"""
    role_enum = None
    if role and role in [r.value for r in UserRole]:
        role_enum = UserRole(role)
    
    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        
        # Получаем все тесты для фильтра
        all_tests = await test_repo.get_all_tests(branch=settings.DEFAULT_BRANCH)
        
        # Получаем результаты
        results = await test_repo.get_all_results(
            branch=settings.DEFAULT_BRANCH,
            role=role_enum,
            test_id=test_id
        )
    
    # Фильтруем по дате если указана
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            results = [r for r in results if r.completed_at >= date_from_dt]
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
            results = [r for r in results if r.completed_at <= date_to_dt]
        except ValueError:
            pass
    
    # Подсчитываем статистику
    total_attempts = len(results)
    passed_count = sum(1 for r in results if r.passed)
    pass_rate = (passed_count / total_attempts * 100) if total_attempts > 0 else 0
    
    return templates.TemplateResponse(
        "stats/index.html",
        {
            "request": request,
            "results": results,
            "all_tests": all_tests,
            "roles": UserRole,
            "current_role": role,
            "current_test_id": test_id,
            "date_from": date_from,
            "date_to": date_to,
            "total_attempts": total_attempts,
            "passed_count": passed_count,
            "pass_rate": pass_rate,
        }
    )
