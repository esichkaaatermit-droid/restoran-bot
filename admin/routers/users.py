from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database.database import async_session_maker
from database.repositories import UserRepository
from database.models import UserRole
from config import settings
from admin.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="admin/templates")


@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request,
    role: Optional[str] = None,
    branch: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Список пользователей"""
    role_enum = None
    if role and role in [r.value for r in UserRole]:
        role_enum = UserRole(role)
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all(role=role_enum, branch=branch)
    
    return templates.TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "users": users,
            "roles": UserRole,
            "current_role": role,
            "current_branch": branch,
            "default_branch": settings.DEFAULT_BRANCH,
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def add_user_form(request: Request, user=Depends(get_current_user)):
    """Форма добавления пользователя"""
    return templates.TemplateResponse(
        "users/add.html",
        {
            "request": request,
            "roles": UserRole,
            "default_branch": settings.DEFAULT_BRANCH,
        }
    )


@router.post("/add")
async def add_user(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    branch: str = Form(...),
    user=Depends(get_current_user)
):
    """Добавление пользователя"""
    try:
        role_enum = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        
        # Проверяем, нет ли уже пользователя с таким телефоном
        existing = await user_repo.get_by_phone_any(phone)
        if existing:
            return templates.TemplateResponse(
                "users/add.html",
                {
                    "request": request,
                    "roles": UserRole,
                    "default_branch": settings.DEFAULT_BRANCH,
                    "error": "Пользователь с таким телефоном уже существует",
                    "form_data": {
                        "full_name": full_name,
                        "phone": phone,
                        "role": role,
                        "branch": branch,
                    }
                }
            )
        
        await user_repo.create(
            full_name=full_name,
            phone=phone,
            role=role_enum,
            branch=branch
        )
    
    return RedirectResponse(url="/users/", status_code=303)


@router.get("/edit/{user_id}", response_class=HTMLResponse)
async def edit_user_form(
    request: Request,
    user_id: int,
    user=Depends(get_current_user)
):
    """Форма редактирования пользователя"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        edit_user = await user_repo.get_by_id(user_id)
    
    if not edit_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "edit_user": edit_user,
            "roles": UserRole,
            "default_branch": settings.DEFAULT_BRANCH,
        }
    )


@router.post("/edit/{user_id}")
async def edit_user(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    branch: str = Form(...),
    is_active: bool = Form(False),
    user=Depends(get_current_user)
):
    """Редактирование пользователя"""
    try:
        role_enum = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.update(
            user_id,
            full_name=full_name,
            phone=phone,
            role=role_enum,
            branch=branch,
            is_active=is_active
        )
    
    return RedirectResponse(url="/users/", status_code=303)


@router.post("/toggle/{user_id}")
async def toggle_user(user_id: int, user=Depends(get_current_user)):
    """Переключить активность пользователя"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_id(user_id)
        if db_user:
            await user_repo.update(user_id, is_active=not db_user.is_active)
    
    return RedirectResponse(url="/users/", status_code=303)
