from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.quest import UserQuestProgress
from src.models.user import User
from src.repositories.user import UserRepository
from src.utils.quest_loader import QuestLoader


class QuestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_current_scene(self, user_id: int, quest_id: str) -> Dict:
        """Получить текущую сцену пользователя (для отображения в UI)"""
        progress = await self.session.execute(
            select(UserQuestProgress.current_scene_id).where(
                and_(
                    UserQuestProgress.user_id == user_id,
                    UserQuestProgress.quest_id == quest_id,
                )
            )
        )
        current_scene_id = progress.scalar()
        if not current_scene_id:
            raise HTTPException(status_code=404, detail="Квест не начат")

        scene = await self.get_scene_by_id(quest_id, current_scene_id)

        return {
            "quest_id": quest_id,
            "scene_id": scene.scene_id,
            "legend": scene.legend,
            "task": scene.task,
            "has_clue": scene.has_clue,
            "tags": scene.tags,
            "is_branching": scene.is_branching,
            "has_clue": scene.has_clue,
        }

    async def submit_answer(
        self, user_id: int, quest_id: str, user_answer: str, is_correct: bool
    ) -> Dict:
        """Обработка ответа пользователя и переход к следующей сцене"""
        progress = await self.session.execute(
            select(UserQuestProgress).where(
                and_(
                    UserQuestProgress.user_id == user_id,
                    UserQuestProgress.quest_id == quest_id,
                )
            )
        )
        progress = progress.scalars().first()
        if not progress:
            raise HTTPException(status_code=404, detail="Квест не начат")

        current_scene = await self.get_scene_by_id(quest_id, progress.current_scene_id)

        if current_scene.is_branching:
            next_scene_id = current_scene.branches.get(
                user_answer, current_scene.default_fail_scene
            )
        else:
            next_scene_id = current_scene.next_scene_id

        if not next_scene_id:
            progress.completed_at = datetime.now()
            await self.session.commit()
            return {"status": "completed", "message": "Квест успешно завершен!"}

        progress.current_scene_id = next_scene_id
        await self.session.commit()

        next_scene = await self.get_scene_by_id(quest_id, next_scene_id)
        return {
            "status": "success",
            "next_scene_id": next_scene_id,
            "legend": next_scene.legend,
            "task": next_scene.task,
            "is_final": next_scene.next_scene_id is None,
        }

    async def _get_user_progress(
        self, user_id: int, quest_id: str
    ) -> Optional[UserQuestProgress]:
        """Внутренний метод получения прогресса"""
        result = await self.session.execute(
            select(UserQuestProgress).where(
                and_(
                    UserQuestProgress.user_id == user_id,
                    UserQuestProgress.quest_id == quest_id,
                )
            )
        )
        return result.scalars().first()

    async def start_quest(self, user_id: int, quest_id: str) -> UserQuestProgress:
        quest_data = QuestLoader.get_quest(quest_id)

        existing = await self._get_user_progress(user_id, quest_id)
        if existing:
            raise HTTPException(status_code=400, detail="Квест уже начат")

        progress = UserQuestProgress(
            user_id=user_id,
            quest_id=quest_id,
            current_scene_id=quest_data["start_scene_id"],
        )
        self.session.add(progress)
        await self.session.commit()
        return progress

    async def get_user_current_scene(self, user_id: int, quest_id: str) -> Dict:
        progress = await self._get_user_progress(user_id, quest_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Квест не начат")

        scene_data = QuestLoader.get_scene(quest_id, progress.current_scene_id)

        return {
            "scene_id": progress.current_scene_id,
            "legend": scene_data.get("legend", ""),
            "task": scene_data.get("task"),
            "has_clue": scene_data.get("has_clue", False),
            "tags": scene_data.get("tags", []),
            "is_branching": scene_data.get("is_branching", False),
            "expected_result": scene_data.get("expected_result"),
            "branches": scene_data.get("branches", {}),
            "default_fail_scene": scene_data.get("default_fail_scene"),
            "next_scene_id": scene_data.get("next_scene_id"),
        }

    async def submit_answer(
        self, user_id: int, quest_id: str, user_answer: str, is_correct: bool
    ) -> Dict:
        progress = await self._get_user_progress(user_id, quest_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Квест не начат")

        scene_data = QuestLoader.get_scene(quest_id, progress.current_scene_id)

        if scene_data.get("is_branching"):
            next_scene_id = scene_data.get("branches", {}).get(
                user_answer, scene_data.get("default_fail_scene")
            )
        else:
            next_scene_id = scene_data.get("next_scene_id")

        if not next_scene_id:
            progress.completed_at = datetime.now()
            await self.session.commit()
            return {"status": "completed"}

        progress.current_scene_id = next_scene_id
        await self.session.commit()

        return {"status": "success", "next_scene_id": next_scene_id}

    async def _validate_quest_exists(self, quest_id: str):
        json_path = Path(f"quests/{quest_id}.json")
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Квест не найден")

    async def get_user_completed_quests(self, user_id: int) -> set[str]:
        """Возвращает множество ID завершенных квестов для пользователя."""
        result = await self.session.execute(
            select(UserQuestProgress.quest_id)
            .where(
                and_(
                    UserQuestProgress.user_id == user_id,
                    UserQuestProgress.completed_at.isnot(None)
                )
            )
        )
        return set(result.scalars().all())

    async def is_task_solved(self, user_id: int, quest_id: str, scene_id: str) -> bool:
        from src.models.quest import QuestTaskSolved
        result = await self.session.execute(
            select(QuestTaskSolved).where(
                and_(
                    QuestTaskSolved.user_id == user_id,
                    QuestTaskSolved.quest_id == quest_id,
                    QuestTaskSolved.scene_id == scene_id,
                )
            )
        )
        return result.scalars().first() is not None

    async def mark_task_solved(self, user_id: int, quest_id: str, scene_id: str, user_query: str):
        from src.models.quest import QuestTaskSolved
        solved = QuestTaskSolved(user_id=user_id, quest_id=quest_id, scene_id=scene_id, user_query=user_query)
        self.session.add(solved)

    async def get_history(self, user_id: int, quest_id: str):
        from src.models.quest import QuestTaskSolved
        result = await self.session.execute(
            select(QuestTaskSolved).where(
                and_(
                    QuestTaskSolved.user_id == user_id,
                    QuestTaskSolved.quest_id == quest_id,
                )
            ).order_by(QuestTaskSolved.created_at)
        )
        return result.scalars().all()

