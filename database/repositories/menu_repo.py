from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MenuItem, MenuType, MenuItemStatus


class MenuRepository:
    """Репозиторий для работы с меню"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_categories(self, menu_type: MenuType, branch: str) -> List[str]:
        """Получить список категорий для типа меню"""
        result = await self.session.execute(
            select(MenuItem.category)
            .where(
                MenuItem.menu_type == menu_type,
                MenuItem.branch == branch,
                MenuItem.status != MenuItemStatus.STOP
            )
            .distinct()
            .order_by(MenuItem.category)
        )
        return [row[0] for row in result.all()]
    
    async def get_items_by_category(
        self,
        category: str,
        menu_type: MenuType,
        branch: str,
        include_stop: bool = False
    ) -> List[MenuItem]:
        """Получить позиции меню по категории"""
        query = select(MenuItem).where(
            MenuItem.category == category,
            MenuItem.menu_type == menu_type,
            MenuItem.branch == branch
        )
        
        if not include_stop:
            query = query.where(MenuItem.status != MenuItemStatus.STOP)
        
        query = query.order_by(MenuItem.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        """Получить позицию по ID"""
        result = await self.session.execute(
            select(MenuItem).where(MenuItem.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_stop_list(self, branch: str) -> List[MenuItem]:
        """Получить стоп-лист"""
        result = await self.session.execute(
            select(MenuItem)
            .where(
                MenuItem.branch == branch,
                MenuItem.status == MenuItemStatus.STOP
            )
            .order_by(MenuItem.menu_type, MenuItem.category, MenuItem.name)
        )
        return list(result.scalars().all())
    
    async def get_go_list(self, branch: str) -> List[MenuItem]:
        """Получить go-лист"""
        result = await self.session.execute(
            select(MenuItem)
            .where(
                MenuItem.branch == branch,
                MenuItem.status == MenuItemStatus.GO
            )
            .order_by(MenuItem.menu_type, MenuItem.category, MenuItem.name)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> MenuItem:
        """Создать позицию меню"""
        item = MenuItem(**kwargs)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def update_status(self, item_id: int, status: MenuItemStatus) -> bool:
        """Обновить статус позиции"""
        await self.session.execute(
            update(MenuItem)
            .where(MenuItem.id == item_id)
            .values(status=status)
        )
        await self.session.commit()
        return True
    
    async def delete_all_by_branch(self, branch: str) -> int:
        """Удалить все позиции меню для филиала (для переимпорта)"""
        result = await self.session.execute(
            delete(MenuItem).where(MenuItem.branch == branch)
        )
        await self.session.commit()
        return result.rowcount
    
    async def bulk_create(self, items: List[dict]) -> int:
        """Массовое создание позиций"""
        for item_data in items:
            item = MenuItem(**item_data)
            self.session.add(item)
        await self.session.commit()
        return len(items)
    
    async def get_all(self, branch: Optional[str] = None) -> List[MenuItem]:
        """Получить все позиции меню"""
        query = select(MenuItem)
        if branch:
            query = query.where(MenuItem.branch == branch)
        query = query.order_by(MenuItem.menu_type, MenuItem.category, MenuItem.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
