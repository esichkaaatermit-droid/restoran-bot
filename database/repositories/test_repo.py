from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Test, Question, Answer, TestResult, UserRole


class TestRepository:
    """Репозиторий для работы с тестами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_tests_by_role(self, role: UserRole, branch: str) -> List[Test]:
        """Получить тесты по роли"""
        result = await self.session.execute(
            select(Test)
            .where(
                Test.role == role,
                Test.branch == branch,
                Test.is_active == True
            )
            .order_by(Test.title)
        )
        return list(result.scalars().all())
    
    async def get_test_with_questions(self, test_id: int) -> Optional[Test]:
        """Получить тест с вопросами и ответами"""
        result = await self.session.execute(
            select(Test)
            .where(Test.id == test_id)
            .options(
                selectinload(Test.questions).selectinload(Question.answers)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_test_by_id(self, test_id: int) -> Optional[Test]:
        """Получить тест по ID"""
        result = await self.session.execute(
            select(Test).where(Test.id == test_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_attempts(self, user_id: int, test_id: int) -> int:
        """Получить количество попыток пользователя"""
        result = await self.session.execute(
            select(func.count(TestResult.id))
            .where(
                TestResult.user_id == user_id,
                TestResult.test_id == test_id
            )
        )
        return result.scalar() or 0
    
    async def save_result(
        self,
        user_id: int,
        test_id: int,
        score: int,
        total_questions: int,
        percent: float,
        passed: bool,
        branch: str
    ) -> TestResult:
        """Сохранить результат теста"""
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            score=score,
            total_questions=total_questions,
            percent=percent,
            passed=passed,
            branch=branch,
            completed_at=datetime.utcnow()
        )
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result
    
    async def get_user_results(self, user_id: int) -> List[TestResult]:
        """Получить результаты пользователя"""
        result = await self.session.execute(
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .options(selectinload(TestResult.test))
            .order_by(TestResult.completed_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_all_results(
        self,
        branch: Optional[str] = None,
        role: Optional[UserRole] = None,
        test_id: Optional[int] = None
    ) -> List[TestResult]:
        """Получить все результаты с фильтрами"""
        query = select(TestResult).options(
            selectinload(TestResult.user),
            selectinload(TestResult.test)
        )
        
        if branch:
            query = query.where(TestResult.branch == branch)
        if test_id:
            query = query.where(TestResult.test_id == test_id)
        
        query = query.order_by(TestResult.completed_at.desc())
        result = await self.session.execute(query)
        results = list(result.scalars().all())
        
        # Фильтруем по роли если нужно
        if role:
            results = [r for r in results if r.user and r.user.role == role]
        
        return results
    
    async def create_test(self, **kwargs) -> Test:
        """Создать тест"""
        test = Test(**kwargs)
        self.session.add(test)
        await self.session.commit()
        await self.session.refresh(test)
        return test
    
    async def add_question(self, test_id: int, text: str, order_num: int = 0) -> Question:
        """Добавить вопрос к тесту"""
        question = Question(test_id=test_id, text=text, order_num=order_num)
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def add_answer(self, question_id: int, text: str, is_correct: bool = False) -> Answer:
        """Добавить вариант ответа"""
        answer = Answer(question_id=question_id, text=text, is_correct=is_correct)
        self.session.add(answer)
        await self.session.commit()
        await self.session.refresh(answer)
        return answer
    
    async def delete_all_by_branch(self, branch: str) -> int:
        """Удалить все тесты для филиала"""
        result = await self.session.execute(
            delete(Test).where(Test.branch == branch)
        )
        await self.session.commit()
        return result.rowcount
    
    async def get_all_tests(self, branch: Optional[str] = None) -> List[Test]:
        """Получить все тесты"""
        query = select(Test)
        if branch:
            query = query.where(Test.branch == branch)
        query = query.order_by(Test.role, Test.title)
        result = await self.session.execute(query)
        return list(result.scalars().all())
