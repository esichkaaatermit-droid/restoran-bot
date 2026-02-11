from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Float,
    BigInteger,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, PyEnum):
    HOSTESS = "hostess"
    WAITER = "waiter"
    BARTENDER = "bartender"
    MANAGER = "manager"


class MenuItemStatus(str, PyEnum):
    NORMAL = "normal"
    STOP = "stop"
    GO = "go"


class MenuType(str, PyEnum):
    KITCHEN = "kitchen"
    BAR = "bar"


class User(Base):
    """Модель пользователя (сотрудника)"""
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_phone", "phone"),
        Index("ix_users_telegram_username", "telegram_username"),
        Index("ix_users_branch_role", "branch", "role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default='Бистро "ГАВРОШ" (Пушкинская 36/69)')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    training_progress: Mapped[List["TrainingProgress"]] = relationship(back_populates="user")
    test_results: Mapped[List["TestResult"]] = relationship(back_populates="user")


class MenuItem(Base):
    """Модель позиции меню"""
    __tablename__ = "menu_items"
    __table_args__ = (
        Index("ix_menu_items_branch_type_category", "branch", "menu_type", "category"),
        Index("ix_menu_items_branch_status", "branch", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    composition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # состав
    weight_volume: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # граммовка/объём
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # Завтраки, Основное меню и т.д.
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Каши, Яйца и т.д.
    menu_type: Mapped[MenuType] = mapped_column(Enum(MenuType), nullable=False)  # кухня или бар
    status: Mapped[MenuItemStatus] = mapped_column(Enum(MenuItemStatus), default=MenuItemStatus.NORMAL)
    photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # путь к фото
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # калории
    proteins: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # белки
    fats: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # жиры
    carbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # углеводы
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default='Бистро "ГАВРОШ" (Пушкинская 36/69)')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrainingMaterial(Base):
    """Модель обучающего материала"""
    __tablename__ = "training_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # текст материала
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # тема: Сервис, Вино и т.д.
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # путь к файлу (PDF/видео)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)  # для какой роли
    order_num: Mapped[int] = mapped_column(Integer, default=0)  # порядок отображения
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default='Бистро "ГАВРОШ" (Пушкинская 36/69)')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    progress: Mapped[List["TrainingProgress"]] = relationship(back_populates="material")


class TrainingProgress(Base):
    """Прогресс изучения материалов"""
    __tablename__ = "training_progress"
    __table_args__ = (
        Index("ix_training_progress_user_material", "user_id", "material_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("training_materials.id"), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="training_progress")
    material: Mapped["TrainingMaterial"] = relationship(back_populates="progress")


class Test(Base):
    """Модель теста для аттестации"""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70)  # проходной балл в процентах
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)  # максимум попыток
    time_per_question: Mapped[int] = mapped_column(Integer, default=30)  # секунд на вопрос
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default='Бистро "ГАВРОШ" (Пушкинская 36/69)')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[List["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    results: Mapped[List["TestResult"]] = relationship(back_populates="test")


class Question(Base):
    """Вопрос теста"""
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    test: Mapped["Test"] = relationship(back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    """Вариант ответа"""
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="answers")


class TestResult(Base):
    """Результат прохождения теста"""
    __tablename__ = "test_results"
    __table_args__ = (
        Index("ix_test_results_user_test", "user_id", "test_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # количество правильных
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    percent: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="test_results")
    test: Mapped["Test"] = relationship(back_populates="results")


class MotivationMessage(Base):
    """Мотивационные сообщения"""
    __tablename__ = "motivation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChecklistItem(Base):
    """Пункт чек-листа для сотрудников"""
    __tablename__ = "checklist_items"
    __table_args__ = (
        Index("ix_checklist_items_branch_role", "branch", "role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, default=0)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default='Бистро "ГАВРОШ" (Пушкинская 36/69)')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
