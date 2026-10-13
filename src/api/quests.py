from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import re

from config import settings
from database import get_db
from src.models.user import User
from src.repositories.quest import QuestRepository
from src.schemas.quest import (
    QuestProgressResponse,
    QuestRunRequest,
    QuestSubmitRequest,
    QuestSubmitResponse,
    SQLResponse,
    QuestsListResponse,
)
from src.utils.auth import get_current_user
from src.utils.sql_executor import SQLExecutor
from src.utils.quest_loader import QuestLoader
from src.utils.scoring_service import ScoringService

router = APIRouter(prefix="/api/quests", tags=["Квесты"])
sql_executor = SQLExecutor(settings.QUEST_DATABASE_URL)


def get_quest_repository(db: AsyncSession = Depends(get_db)) -> QuestRepository:
    return QuestRepository(db)


def _extract_update_value(sql_query: str) -> str:
    """Упрощенный парсер для извлечения значения из UPDATE запроса."""
    match = re.search(
        r"SET\s+\w+\s*=\s*'?(.*?)'?\s*(?:WHERE|$|;)", sql_query, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return ""

@router.get(
    "",
    summary="Получение списка всех квестов",
    response_model=QuestsListResponse,
)
async def get_all_quests(
    current_user: User = Depends(get_current_user),
    repo: QuestRepository = Depends(get_quest_repository),
):
    all_quests = QuestLoader.get_all_quests()

    completed_quests = await repo.get_user_completed_quests(current_user.user_id)

    quests_response = []
    for q in all_quests:
        quests_response.append({
            "id": q["id"],
            "title": q["title"],
            "description": q["description"],
            "is_completed": q["id"] in completed_quests
        })

    return {"quests": quests_response}


@router.get(
    "/{quest_id}/progress",
    summary="Инициализация или продолжение квеста",
    response_model=dict,
)
async def get_quest_progress(
    quest_id: str,
    current_user: User = Depends(get_current_user),
    repo: QuestRepository = Depends(get_quest_repository),
):
    try:
        scene_data = await repo.get_user_current_scene(current_user.user_id, quest_id)
    except HTTPException as e:
        if e.status_code == 404:
            await repo.start_quest(current_user.user_id, quest_id)
            scene_data = await repo.get_user_current_scene(
                current_user.user_id, quest_id
            )
        else:
            raise e

    # Вычисление прогресса
    quest_meta = QuestLoader.get_quest(quest_id)
    total_scenes = len(quest_meta.get("scenes", {}))
    # В идеале нужно считать пройденные, но пока так:
    history = await repo.get_history(current_user.user_id, quest_id)
    percent = round((len(history) / total_scenes) * 100) if total_scenes > 0 else 0

    return {
        "scene_id": scene_data["scene_id"],
        "legend": scene_data["legend"],
        "task": scene_data["task"],
        "has_clue": scene_data["has_clue"],
        "total_scenes": total_scenes,
        "completed_scenes": len(history),
        "percent_completed": percent
    }


@router.get(
    "/{quest_id}/history",
    summary="Получение истории решений квеста",
)
async def get_quest_history(
    quest_id: str,
    current_user: User = Depends(get_current_user),
    repo: QuestRepository = Depends(get_quest_repository),
):
    history = await repo.get_history(current_user.user_id, quest_id)
    result = []
    for h in history:
        result.append({
            "scene_id": h.scene_id,
            "user_query": h.user_query,
            "created_at": h.created_at
        })
    return {"history": result}


@router.post(
    "/{quest_id}/run",
    summary="Выполнение SQL запроса в квесте",
    response_model=SQLResponse,
)
async def run_quest_sql(
    quest_id: str,
    request: QuestRunRequest,
    current_user: User = Depends(get_current_user),
    repo: QuestRepository = Depends(get_quest_repository),
):
    scene_data = await repo.get_user_current_scene(current_user.user_id, quest_id)
    if scene_data["scene_id"] != request.scene_id:
        raise HTTPException(status_code=400, detail="Неверная сцена для выполнения")

    try:
        if scene_data["is_branching"]:
            raise HTTPException(
            status_code=403, detail=f"Пока низя"
            )
        return await sql_executor.execute_sql(request.sql_query, allow_star=True)
    except HTTPException as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка выполнения: {str(e.detail)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post(
    "/{quest_id}/submit",
    summary="Отправка решения квеста на проверку",
    response_model=dict,
)
async def submit_quest_solution(
    quest_id: str,
    request: QuestSubmitRequest,
    current_user: User = Depends(get_current_user),
    repo: QuestRepository = Depends(get_quest_repository),
    db: AsyncSession = Depends(get_db),
):
    scene = await repo.get_user_current_scene(current_user.user_id, quest_id)
    scene_id = scene["scene_id"]
    
    already_solved = await repo.is_task_solved(current_user.user_id, quest_id, scene_id)
    if already_solved:
        return {
            "is_correct": True,
            "points": {"earned": 0, "penalty": 0},
            "is_quest_completed": False,
            "message": "Задача уже решена"
        }

    user_answer_value = ""
    is_correct = False

    try:
        if scene["is_branching"]:
            user_answer_value = _extract_update_value(request.sql_query)
            target_table = scene.get("expected_result", {}).get("target_table")
            if target_table:
                # Check safely via transaction rollback
                await sql_executor.simulate_update(request.sql_query, allowed_tables=[target_table])
            is_correct = user_answer_value in scene.get("branches", {})
        else:
            if scene.get("expected_result"):
                user_result = await sql_executor.execute_sql(request.sql_query)
                expected = scene["expected_result"]
                user_data = user_result.get("data", [])
                expected_data = expected.get("data", [])
                try:
                    is_correct = sorted(user_data) == sorted(expected_data)
                except TypeError:
                    is_correct = user_data == expected_data
            else:
                is_correct = True
    except (HTTPException, Exception):
        is_correct = False

    is_quest_completed = False
    scoring_service = ScoringService(db)

    try:
        if is_correct:
            result = await repo.submit_answer(
                user_id=current_user.user_id,
                quest_id=quest_id,
                user_answer=user_answer_value,
                is_correct=is_correct,
            )
            await repo.mark_task_solved(current_user.user_id, quest_id, scene_id, request.sql_query)
            await scoring_service.add_points(current_user.user_id, 100)
            is_quest_completed = result.get("status") == "completed"
            
            # Log event
            from src.models.user_event import UserEvent
            event = UserEvent(user_id=current_user.user_id, event_type="quest_task_solved", payload={"quest_id": quest_id, "scene_id": scene_id, "is_correct": True})
            db.add(event)
        else:
            await scoring_service.deduct_points(current_user.user_id, 10)
            from src.models.user_event import UserEvent
            event = UserEvent(user_id=current_user.user_id, event_type="quest_task_failed", payload={"quest_id": quest_id, "scene_id": scene_id, "is_correct": False})
            db.add(event)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "is_correct": is_correct,
        "points": {
            "earned": 100 if is_correct else 0,
            "penalty": 0 if is_correct else 10,
        },
        "is_quest_completed": is_quest_completed,
        "awarded_achievements": [],
    }
