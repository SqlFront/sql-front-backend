from fastapi import Depends

from database import get_db
from src.repositories.achievement import AchievementRepository
from src.repositories.progress import ProgressRepository
from src.repositories.task import TaskRepository
from src.repositories.user import UserRepository


async def get_user_repository(session=Depends(get_db)) -> UserRepository:
    return UserRepository(session)


async def get_progress_repository(session=Depends(get_db)) -> ProgressRepository:
    return ProgressRepository(session)


async def get_achievement_repository(session=Depends(get_db)) -> AchievementRepository:
    return AchievementRepository(session)


async def get_task_repository(session=Depends(get_db)) -> TaskRepository:
    return TaskRepository(session)
