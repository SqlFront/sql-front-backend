from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy import delete, desc, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from src.models.clue import PurchasedClue
from src.models.progress import UserProgress
from src.models.task import Task, TaskSolved
from src.models.user import User
from src.repositories.achievement import AchievementRepository
from src.repositories.user import UserRepository
from src.utils.scoring_service import ScoringService

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tasks_count(self) -> dict:
        """Возвращает количество задач по уровням сложности"""
        result = await self.session.execute(
            select(Task.mission_id, func.count(Task.task_id)).group_by(Task.mission_id)
        )
        counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for mission_id, count in result.all():
            counts[mission_id] = count
        return {
            "easy_tasks_total": counts[0],
            "medium_tasks_total": counts[1],
            "hard_tasks_total": counts[2],
            "mission3_tasks_total": counts[3],
            "mission4_tasks_total": counts[4],
            "mission5_tasks_total": counts[5],
        }

    async def get_task_info(self, mission_id: int, task_id: int) -> Task:
        """Возвращает информацию о задаче"""
        result = await self.session.execute(
            select(Task).where(
                (Task.mission_id == mission_id) & (Task.task_id == task_id)
            )
        )
        return result.scalars().first()

    async def add_solved_task(self, user_id: int, task_id: int) -> TaskSolved:
        """Добавляет запись о решенной задаче"""
        solved_task = TaskSolved(
            user_id=user_id, task_global_id=task_id, solved_at=datetime.now()
        )
        self.session.add(solved_task)
        await self.session.commit()
        return solved_task

    async def get_all_tasks_grouped(self) -> Dict[int, List[dict]]:
        """Возвращает все задания, сгруппированные по mission_id"""
        result = await self.session.execute(
            select(
                Task.mission_id, Task.task_id, Task.task_global_id, Task.title
            ).order_by(Task.mission_id, Task.task_id)
        )
        grouped = defaultdict(list)
        for task in result.all():
            grouped[task.mission_id].append(
                {
                    "task_id": task.task_id,
                    "task_global_id": task.task_global_id,
                    "title": task.title,
                }
            )
        return dict(grouped)

    async def get_all_tasks_grouped_with_status(
        self, user_id: int
    ) -> Dict[int, List[dict]]:
        req = (
            select(
                Task.mission_id,
                Task.task_id,
                Task.task_global_id,
                Task.title,
                TaskSolved.task_global_id.isnot(None).label("is_solved"),
            )
            .select_from(Task)
            .join(
                TaskSolved,
                (Task.task_global_id == TaskSolved.task_global_id)
                & (TaskSolved.user_id == user_id),
                isouter=True,
            )
            .order_by(Task.mission_id, Task.task_id)
        )
        result = await self.session.execute(req)
        grouped = defaultdict(list)
        for row in result.all():
            grouped[row.mission_id].append(
                {
                    "task_id": row.task_id,
                    "task_global_id": row.task_global_id,
                    "title": row.title,
                    "is_solved": bool(row.is_solved),
                }
            )
        return dict(grouped)

    async def get_user_solved_tasks(self, user_id: int) -> Dict[int, List[dict]]:
        """Возвращает решенные пользователем задания, сгруппированные по mission_id"""
        result = await self.session.execute(
            select(Task.mission_id, Task.task_id, Task.task_global_id, Task.title)
            .join(TaskSolved, Task.task_global_id == TaskSolved.task_global_id)
            .where(TaskSolved.user_id == user_id)
            .order_by(Task.mission_id, Task.task_id)
        )
        grouped = defaultdict(list)
        for task in result.all():
            grouped[task.mission_id].append(
                {
                    "task_id": task.task_id,
                    "task_global_id": task.task_global_id,
                    "title": task.title,
                }
            )
        return dict(grouped)

    async def get_tasks_grouped_by_mission(self, user_id: int) -> Dict[int, List[dict]]:
        stmt = (
            select(
                Task.mission_id,
                Task.task_id,
                Task.task_global_id,
                Task.title,
                TaskSolved.task_global_id.isnot(None).label("is_solved"),
            )
            .select_from(Task)
            .join(
                TaskSolved,
                (Task.task_global_id == TaskSolved.task_global_id)
                & (TaskSolved.user_id == user_id),
                isouter=True,
            )
            .order_by(Task.mission_id, Task.task_id)
        )
        result = await self.session.execute(stmt)
        grouped = defaultdict(list)
        for row in result:
            grouped[row.mission_id].append(
                {
                    "task_id": row.task_id,
                    "task_global_id": row.task_global_id,
                    "title": row.title,
                    "is_solved": bool(row.is_solved),
                }
            )
        return dict(grouped)

    async def get_task_info_with_status(
        self, mission_id: int, task_id: int, user_id: int
    ) -> tuple[Task, bool]:
        """Возвращает задачу и статус решения пользователем"""
        task_result = await self.session.execute(
            select(Task).where(
                (Task.mission_id == mission_id) & (Task.task_id == task_id)
            )
        )
        task = task_result.scalars().first()
        if not task:
            return None, False
        solved_result = await self.session.execute(
            select(
                exists().where(
                    (TaskSolved.task_global_id == task.task_global_id)
                    & (TaskSolved.user_id == user_id)
                )
            )
        )
        is_solved = solved_result.scalar()

        return task, is_solved

    async def check_and_reward_task(
        self, user_id: int, mission_id: int, task_id: int, is_correct: bool
    ) -> dict:

        task_data = await self._get_task_data(mission_id, task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task_global_id, tags = task_data

        already_solved = await self._check_already_solved(user_id, task_global_id)

        points_earned = 0
        points_penalty = 0
        message = ""

        scoring_service = ScoringService(self.session)
        user_repo = UserRepository(self.session)
        user = await user_repo.get_user_by_id(user_id)
        user_progress = await user_repo.get_user_progress_by_id(user_id)

        if is_correct:
            if not already_solved:
                points_earned = self._get_base_points(mission_id)
                await scoring_service.add_points(user_id, points_earned)
                await self.add_solved_task(user_id, task_global_id)
                
                # Update progress
                if user_progress:
                    if mission_id == 0:
                        user_progress.easy_tasks_solved += 1
                    elif mission_id == 1:
                        user_progress.medium_tasks_solved += 1
                    elif mission_id == 2:
                        user_progress.hard_tasks_solved += 1
                        
                message = f"Правильно! Заработано {points_earned} баллов"
            else:
                message = "Правильно! За повторное решение баллы не начисляются"
        else:
            if not already_solved:
                points_penalty = int(self._get_base_points(mission_id) * 0.1)
                actual_penalty = min(points_penalty, user.total_score if user else 0)
                await scoring_service.deduct_points(user_id, actual_penalty)
                if actual_penalty > 0:
                    message = f"Ответ неверный! Списано {actual_penalty} баллов"
                else:
                    message = "Ответ неверный!"
            else:
                message = "Ответ неверный! За повторное решение баллы не списываются"

        awarded_achievements = []
        if is_correct and tags and not already_solved:
            achievement_repo = AchievementRepository(self.session)
            awarded_achievements = await achievement_repo.check_and_award_achievements(
                user_id=user_id, task_tags=tags
            )

        current_points = user.total_score if user and user.total_score is not None else 0
        if is_correct and not already_solved:
            current_points += points_earned
        elif not is_correct and not already_solved:
            current_points = max(0, current_points - actual_penalty)

        await self.session.commit()

        return {
            "was_solved_before": already_solved,
            "points_earned": points_earned,
            "points_penalty": points_penalty,
            "message": message,
            "awarded_achievements": awarded_achievements,
            "current_points": current_points,
        }

    async def purchase_clue(
        self, user_id: int, task_global_id: int, clue_type: int, cost: int
    ) -> tuple[int, int]:
        already_solved = await self._check_already_solved(user_id, task_global_id)
        if already_solved:
            cost = 0

        user = await self.session.get(User, user_id)
        if user.total_score < cost:
            raise HTTPException(
                status_code=400, detail="Недостаточно баллов для покупки подсказки"
            )
        user.total_score -= cost

        self.session.add(
            PurchasedClue(
                user_id=user_id, task_global_id=task_global_id, clue_type=clue_type
            )
        )
        await self.session.commit()
        return cost, user.total_score

    async def clear_purchased_clues(self, user_id: int, task_global_id: int):
        await self.session.execute(
            delete(PurchasedClue).where(
                (PurchasedClue.user_id == user_id)
                & (PurchasedClue.task_global_id == task_global_id)
            )
        )

    async def get_task_stats(self) -> list[dict]:
        """Возвращает статистику по решенным задачам."""
        query = (
            select(TaskSolved.task_global_id, func.count().label("total_solved"))
            .group_by(TaskSolved.task_global_id)
            .order_by(func.count().desc())
        )
        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings()]

    async def find_next_task_data(self, mission_id, task_id):
        """Возвращает id миссии и задачи для следующей задачи"""
        next_probable_task_id = task_id + 1
        next_task_exists = await self.session.execute(
            select(Task).where(
                (Task.mission_id == mission_id)
                & (Task.task_id == next_probable_task_id)
            )
        )
        if next_task_exists.scalars().first():
            return (mission_id, next_probable_task_id)
        next_probable_task_id = 1
        next_probable_mission_id = mission_id + 1
        next_mission_exists = await self.session.execute(
            select(Task).where(
                (Task.mission_id == next_probable_mission_id)
                & (Task.task_id == next_probable_task_id)
            )
        )
        if next_mission_exists.scalars().first():
            return (next_probable_mission_id, next_probable_task_id)
        return (None, None)

    async def find_prev_task_data(self, mission_id, task_id):
        """Возвращает id миссии и задачи для предыдущей задачи"""
        prev_probable_task_id = task_id - 1
        prev_task_exists = await self.session.execute(
            select(Task).where(
                (Task.mission_id == mission_id)
                & (Task.task_id == prev_probable_task_id)
            )
        )
        if prev_task_exists.scalars().first():
            return (mission_id, prev_probable_task_id)
        if mission_id == 0:
            return (None, None)
        prev_probable_mission_id = mission_id - 1
        prev_mission_exists = await self.session.execute(
            select(Task.task_id)
            .where(Task.mission_id == prev_probable_mission_id)
            .order_by(Task.task_id.desc())
        )
        prev_task_id = prev_mission_exists.scalars().first()
        if prev_task_id:
            return (prev_probable_mission_id, prev_task_id)
        return (None, None)

    async def _get_task_data(self, mission_id: int, task_id: int) -> tuple | None:
        """Возвращает (task_global_id, tags) за один запрос"""
        result = await self.session.execute(
            select(Task.task_global_id, Task.tags).where(
                (Task.mission_id == mission_id) & (Task.task_id == task_id)
            )
        )
        row = result.first()
        return (row.task_global_id, row.tags or []) if row else None

    async def _check_already_solved(self, user_id: int, task_global_id: int) -> bool:
        result = await self.session.execute(
            select(exists().where(
                (TaskSolved.user_id == user_id) & 
                (TaskSolved.task_global_id == task_global_id)
            ))
        )
        return result.scalar()

    def _get_base_points(self, mission_id: int) -> int:
        if 0 <= mission_id < len(settings.TASK_POINTS):
            return settings.TASK_POINTS[mission_id]
        return 0
