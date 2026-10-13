from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from src.api.dependencies import get_task_repository
from src.models.clue import PurchasedClue
from src.models.user import User
from src.repositories.task import TaskRepository
from src.schemas.task import (
    GroupedTasksResponse,
    MissionsResponse,
    SQLRequest,
    SQLResponse,
    TaskClue,
    TaskExpectedResult,
    TasksCount,
    TaskSubmissionResult,
    TaskWithStatusResponse,
)
from src.utils.analytics import log_user_event
from src.utils.auth import get_current_user
from src.utils.sql_executor import SQLExecutor
from src.utils import catalog_model

router = APIRouter(prefix="/api/missions", tags=["Миссии и задачи"])
sql_executor = SQLExecutor(settings.GAME_DATABASE_URL)


def _reveal_expected(task):
    """Скрывает реальный ожидаемый результат для модельных задач."""
    payload = task.expected_result
    if isinstance(payload, dict):
        if payload.get("mode") == "model":
            return {
                "columns": ["Что проверяется:"],
                "data": [[payload.get("reveal", "")]],
                "row_count": 1,
            }
        elif payload.get("mode") in ("ddl", "plpgsql"):
            return {
                "columns": payload.get("columns", ["Результат"]),
                "data": payload.get("data", [["Успешная проверка DDL"]]),
                "row_count": len(payload.get("data", [1])),
            }
    return payload


@router.get(
    "/get_info",
    summary="Количество задач по категориям",
    tags=["Профиль"],
    response_model=TasksCount,
)
async def get_tasks_count(db: AsyncSession = Depends(get_db)):
    repo = TaskRepository(db)
    return await repo.get_tasks_count()


@router.get(
    "/{mission_id}/tasks/{task_id}",
    summary="Основная информация о задаче",
    response_model=TaskWithStatusResponse,
)
async def get_task_info(
    mission_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    task, is_solved = await repo.get_task_info_with_status(
        mission_id, task_id, current_user.user_id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    purchased_clue1 = await repo.session.execute(
        select(PurchasedClue.clue_type).where(
            (PurchasedClue.user_id == current_user.user_id)
            & (PurchasedClue.task_global_id == task.task_global_id)
            & (PurchasedClue.clue_type == 1)
        )
    )
    purchased_clue2 = await repo.session.execute(
        select(PurchasedClue.clue_type).where(
            (PurchasedClue.user_id == current_user.user_id)
            & (PurchasedClue.task_global_id == task.task_global_id)
            & (PurchasedClue.clue_type == 2)
        )
    )
    has_clue1 = purchased_clue1.scalar_one_or_none()
    has_clue2 = purchased_clue2.scalar_one_or_none()

    prev_mission_id, prev_task_id = await repo.find_prev_task_data(mission_id, task_id)
    next_mission_id, next_task_id = await repo.find_next_task_data(mission_id, task_id)

    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type="task_started",
        task_id=task.task_global_id,
        payload={"mission_id": mission_id, "task_id": task_id},
    )

    difficulty = None
    if task.tags:
        for d in ["easy", "medium", "hard"]:
            if d in task.tags:
                difficulty = d
                break

    return {
        "task_id": task.task_id,
        "mission_id": task.mission_id,
        "title": task.title,
        "description": task.description,
        "is_solved": is_solved,
        "has_clue1": bool(has_clue1),
        "has_clue2": bool(has_clue2),
        "previous": {"mission_id": prev_mission_id, "task_id": prev_task_id},
        "next": {"mission_id": next_mission_id, "task_id": next_task_id},
        "difficulty": difficulty,
    }


@router.post(
    "/{mission_id}/tasks/{task_id}/clue",
    summary="Купить текстовую подсказку",
    tags=["Подсказки"],
)
async def purchase_clue(
    mission_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
    db: AsyncSession = Depends(get_db),
):
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача на найдена")
    cost = int(settings.TASK_POINTS[mission_id] * 0.1)
    purchased_clue1 = await repo.session.execute(
        select(PurchasedClue.clue_type).where(
            (PurchasedClue.user_id == current_user.user_id)
            & (PurchasedClue.task_global_id == task.task_global_id)
            & (PurchasedClue.clue_type == 1)
        )
    )
    has_clue1 = purchased_clue1.scalar_one_or_none()
    if has_clue1:
        return {
            "points_spent": 0,
            "total_score": current_user.total_score,
            "clue": task.clue,
        }
    actual_cost, new_total = await repo.purchase_clue(
        user_id=current_user.user_id,
        task_global_id=task.task_global_id,
        clue_type=1,
        cost=cost,
    )
    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type="purchase_clue",
        task_id=task.task_global_id,
        payload={"mission_id": mission_id, "task_id": task_id, "clue_type": 1},
    )
    return {
        "points_spent": actual_cost,
        "total_score": new_total,
        "clue": task.clue,
    }


@router.post(
    "/{mission_id}/tasks/{task_id}/expected_result",
    summary="Купить ожидаемый результат",
    tags=["Подсказки"],
)
async def purchase_expected_result(
    mission_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
    db: AsyncSession = Depends(get_db),
):
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача на найдена")
    cost = int(settings.TASK_POINTS[mission_id] * 0.2)
    purchased_clue2 = await repo.session.execute(
        select(PurchasedClue.clue_type).where(
            (PurchasedClue.user_id == current_user.user_id)
            & (PurchasedClue.task_global_id == task.task_global_id)
            & (PurchasedClue.clue_type == 2)
        )
    )
    has_clue2 = purchased_clue2.scalar_one_or_none()
    if has_clue2:
        return {
            "points_spent": 0,
            "total_score": current_user.total_score,
            "expected_result": _reveal_expected(task),
        }
    actual_cost, new_total = await repo.purchase_clue(
        user_id=current_user.user_id,
        task_global_id=task.task_global_id,
        clue_type=2,
        cost=cost,
    )
    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type="purchase_clue",
        task_id=task.task_global_id,
        payload={"mission_id": mission_id, "task_id": task_id, "clue_type": 2},
    )
    return {
        "points_spent": actual_cost,
        "total_score": new_total,
        "expected_result": _reveal_expected(task),
    }


@router.post(
    "/{mission_id}/tasks/{task_id}/run",
    summary="Выполнение SQL",
    response_model=SQLResponse,
)
async def run_sql_query(
    mission_id: int,
    task_id: int,
    request: SQLRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    try:
        await log_user_event(
            session=db,
            user_id=current_user.user_id,
            event_type="task_attempt",
            task_id=task.task_global_id,
            payload={"mission_id": mission_id, "task_id": task_id},
        )
        exp_res = task.expected_result or {}
        if exp_res.get("mode") == "model":
            ok, message = catalog_model.verify(
                request.sql_query, exp_res
            )
            return {"columns": ["Результат:"], "data": [[message]], "row_count": 1}
        elif exp_res.get("mode") in ("ddl", "plpgsql"):
            test_query = exp_res.get("test_query", "")
            expect_error = exp_res.get("expect_error", False)
            return await sql_executor.simulate_ddl(
                request.sql_query, test_query, expect_error=expect_error
            )
        return await sql_executor.execute_sql(request.sql_query, allow_star=True)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f"Runtime error: {str(e.detail)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/{mission_id}/tasks/{task_id}/submit",
    summary="Проверка ответа",
    response_model=TaskSubmissionResult,
)
async def submit_sql_query(
    mission_id: int,
    task_id: int,
    request: SQLRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    expected_result = task.expected_result
    if not expected_result:
        raise HTTPException(
            status_code=404, detail="Для этой задачи еще не добавлен ответ"
        )

    hint = ""
    user_result = {}
    try:
        if expected_result.get("mode") == "model":
            is_correct, hint = catalog_model.verify(request.sql_query, expected_result)
        elif expected_result.get("mode") in ("ddl", "plpgsql"):
            test_query = expected_result.get("test_query", "")
            expect_error = expected_result.get("expect_error", False)
            user_result = await sql_executor.simulate_ddl(
                request.sql_query, test_query, expect_error=expect_error
            )
            if expect_error:
                is_correct = user_result.get("error_caught", False)
                hint = "Триггер успешно заблокировал некорректную операцию" if is_correct else ""
            else:
                user_data = user_result.get("data", [])
                expected_data = expected_result.get("data", [])
                try:
                    is_correct = sorted(user_data) == sorted(expected_data)
                except TypeError:
                    is_correct = user_data == expected_data
        else:
            user_result = await sql_executor.execute_sql(request.sql_query)
            user_data = user_result.get("data", [])
            expected_data = expected_result.get("data", [])
            try:
                is_correct = sorted(user_data) == sorted(expected_data)
            except TypeError:
                is_correct = user_data == expected_data
    except HTTPException as e:
        is_correct = False
        hint = str(e.detail)
    except Exception as e:
        is_correct = False
        hint = f"Ошибка выполнения запроса: {str(e)}"
    try:
        result = await repo.check_and_reward_task(
            user_id=current_user.user_id,
            mission_id=mission_id,
            task_id=task_id,
            is_correct=is_correct,
        )
        await log_user_event(
            session=db,
            user_id=current_user.user_id,
            event_type="task_submitted",
            task_id=task.task_global_id,
            payload={
                "mission_id": mission_id,
                "task_id": task_id,
                "is_correct": is_correct,
            },
        )
        return {
            **result, 
            "is_correct": is_correct,
            "columns": user_result.get("columns", []),
            "data": user_result.get("data", []),
            "hint": hint,
        }

    except IndexError:
        raise HTTPException(
            status_code=400,
            detail="Некорректный mission_id: отсутствует в TASK_POINTS (config.py)",
        )


@router.get("/", summary="Задачи со статусом решения", response_model=MissionsResponse)
async def get_tasks_grouped(
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
):
    grouped_tasks = await repo.get_tasks_grouped_by_mission(current_user.user_id)
    return {"missions": grouped_tasks}
