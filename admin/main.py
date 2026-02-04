import asyncio
import uvicorn

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from database.database import init_db
from admin.routers import users_router, import_router, stats_router
from admin.auth import get_current_user

app = FastAPI(
    title="Бистро ГАВРОШ - Админ-панель",
    description="Административная панель для управления ботом персонала",
    version="1.0.0"
)

# Подключаем шаблоны
templates = Jinja2Templates(directory="admin/templates")

# Подключаем роутеры
app.include_router(users_router)
app.include_router(import_router)
app.include_router(stats_router)


@app.on_event("startup")
async def startup():
    """Инициализация при запуске"""
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_current_user)):
    """Главная страница"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "admin.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
