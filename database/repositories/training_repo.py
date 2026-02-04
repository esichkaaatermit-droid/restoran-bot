from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TrainingMaterial, TrainingProgress, UserRole


class TrainingRepository:
    """Репозиторий для работы с обучающими материалами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_materials_by_role(self, role: UserRole, branch: str) -> List[TrainingMaterial]:
        """Получить материалы по роли"""
        result = await self.session.execute(
            select(TrainingMaterial)
            .where(
                TrainingMaterial.role == role,
                TrainingMaterial.branch == branch
            )
            .order_by(TrainingMaterial.order_num, TrainingMaterial.title)
        )
        return list(result.scalars().all())
    
    async def get_material_by_id(self, material_id: int) -> Optional[TrainingMaterial]:
        """Получить материал по ID"""
        result = await self.session.execute(
            select(TrainingMaterial).where(TrainingMaterial.id == material_id)
        )
        return result.scalar_one_or_none()
    
    async def get_progress(self, user_id: int, material_id: int) -> Optional[TrainingProgress]:
        """Получить прогресс пользователя по материалу"""
        result = await self.session.execute(
            select(TrainingProgress)
            .where(
                TrainingProgress.user_id == user_id,
                TrainingProgress.material_id == material_id
            )
        )
        return result.scalar_one_or_none()
    
    async def mark_completed(self, user_id: int, material_id: int) -> TrainingProgress:
        """Отметить материал как изученный"""
        progress = await self.get_progress(user_id, material_id)
        
        if progress:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
        else:
            progress = TrainingProgress(
                user_id=user_id,
                material_id=material_id,
                is_completed=True,
                completed_at=datetime.utcnow()
            )
            self.session.add(progress)
        
        await self.session.commit()
        await self.session.refresh(progress)
        return progress
    
    async def get_user_progress(self, user_id: int) -> List[TrainingProgress]:
        """Получить весь прогресс пользователя"""
        result = await self.session.execute(
            select(TrainingProgress)
            .where(TrainingProgress.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> TrainingMaterial:
        """Создать обучающий материал"""
        material = TrainingMaterial(**kwargs)
        self.session.add(material)
        await self.session.commit()
        await self.session.refresh(material)
        return material
    
    async def delete_all_by_branch(self, branch: str) -> int:
        """Удалить все материалы для филиала"""
        result = await self.session.execute(
            delete(TrainingMaterial).where(TrainingMaterial.branch == branch)
        )
        await self.session.commit()
        return result.rowcount
    
    async def bulk_create(self, materials: List[dict]) -> int:
        """Массовое создание материалов"""
        for mat_data in materials:
            material = TrainingMaterial(**mat_data)
            self.session.add(material)
        await self.session.commit()
        return len(materials)
    
    async def get_all(self, branch: Optional[str] = None) -> List[TrainingMaterial]:
        """Получить все материалы"""
        query = select(TrainingMaterial)
        if branch:
            query = query.where(TrainingMaterial.branch == branch)
        query = query.order_by(TrainingMaterial.role, TrainingMaterial.order_num)
        result = await self.session.execute(query)
        return list(result.scalars().all())
