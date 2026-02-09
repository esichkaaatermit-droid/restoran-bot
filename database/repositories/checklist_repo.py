from typing import List, Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ChecklistItem, UserRole


class ChecklistRepository:
    """Репозиторий для работы с чек-листами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_role(self, role: UserRole, branch: str) -> List[ChecklistItem]:
        """Получить чек-лист по роли"""
        result = await self.session.execute(
            select(ChecklistItem)
            .where(
                ChecklistItem.role == role,
                ChecklistItem.branch == branch,
            )
            .order_by(ChecklistItem.category, ChecklistItem.order_num)
        )
        return list(result.scalars().all())

    async def get_categories_by_role(self, role: UserRole, branch: str) -> List[str]:
        """Получить список категорий чек-листа для роли"""
        result = await self.session.execute(
            select(ChecklistItem.category)
            .where(
                ChecklistItem.role == role,
                ChecklistItem.branch == branch,
                ChecklistItem.category.isnot(None),
            )
            .distinct()
            .order_by(ChecklistItem.category)
        )
        return [row[0] for row in result.all() if row[0]]

    async def get_by_category(
        self, role: UserRole, category: str, branch: str
    ) -> List[ChecklistItem]:
        """Получить задачи чек-листа по категории"""
        result = await self.session.execute(
            select(ChecklistItem)
            .where(
                ChecklistItem.role == role,
                ChecklistItem.category == category,
                ChecklistItem.branch == branch,
            )
            .order_by(ChecklistItem.order_num)
        )
        return list(result.scalars().all())

    async def delete_all_by_branch(self, branch: str) -> int:
        """Удалить все пункты чек-листа для филиала"""
        result = await self.session.execute(
            delete(ChecklistItem).where(ChecklistItem.branch == branch)
        )
        await self.session.commit()
        return result.rowcount

    async def bulk_create(self, items: List[dict]) -> int:
        """Массовое создание пунктов чек-листа"""
        for item_data in items:
            item = ChecklistItem(**item_data)
            self.session.add(item)
        await self.session.commit()
        return len(items)

    async def count_by_role(self, role: UserRole, branch: Optional[str] = None) -> int:
        """Подсчитать количество пунктов по роли"""
        query = select(func.count(ChecklistItem.id)).where(ChecklistItem.role == role)
        if branch:
            query = query.where(ChecklistItem.branch == branch)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_all(self, branch: Optional[str] = None) -> List[ChecklistItem]:
        """Получить все пункты чек-листа"""
        query = select(ChecklistItem)
        if branch:
            query = query.where(ChecklistItem.branch == branch)
        query = query.order_by(ChecklistItem.role, ChecklistItem.category, ChecklistItem.order_num)
        result = await self.session.execute(query)
        return list(result.scalars().all())
