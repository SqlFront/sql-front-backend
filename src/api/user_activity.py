from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from src.api.dependencies import get_task_repository
from src.models.user import User
from src.repositories.task import TaskRepository
from src.utils.analytics import log_user_event
from src.utils.auth import get_current_user

router = APIRouter(prefix="/util", tags=["Телеметрия"])


class PastePayload(BaseModel):
    length: int
    preview: Optional[str] = None


class GenericTelemetryPayload(BaseModel):
    event_type: str
    payload: Optional[Dict[str, Any]] = None


@router.post(
    "/{mission_id}/tasks/{task_id}/inactive",
    summary="Пользователь покинул страницу (переключил вкладку или свернул окно)",
)
async def log_user_inactive(
    mission_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
    db: AsyncSession = Depends(get_db),
):
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type="user_inactive",
        task_id=task.task_global_id,
        payload={"mission_id": mission_id, "task_id": task_id},
    )
    return {"status": "ok", "event": "user_inactive"}


@router.post(
    "/{mission_id}/tasks/{task_id}/paste",
    summary="Фиксация вставки кода из буфера обмена",
)
async def log_user_paste(
    mission_id: int,
    task_id: int,
    data: PastePayload,
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
    db: AsyncSession = Depends(get_db),
):
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type="code_pasted",
        task_id=task.task_global_id,
        payload={
            "mission_id": mission_id,
            "task_id": task_id,
            "length": data.length,
            "preview": data.preview[:50] if data.preview else "",
        },
    )
    return {"status": "ok", "event": "code_pasted"}


@router.post(
    "/{mission_id}/tasks/{task_id}/telemetry",
    summary="Универсальный прием событий телеметрии решения задачи",
)
async def log_user_telemetry(
    mission_id: int,
    task_id: int,
    data: GenericTelemetryPayload,
    current_user: User = Depends(get_current_user),
    repo: TaskRepository = Depends(get_task_repository),
    db: AsyncSession = Depends(get_db),
):
    task = await repo.get_task_info(mission_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    payload = {"mission_id": mission_id, "task_id": task_id}
    if data.payload:
        payload.update(data.payload)

    await log_user_event(
        session=db,
        user_id=current_user.user_id,
        event_type=data.event_type,
        task_id=task.task_global_id,
        payload=payload,
    )
    return {"status": "ok", "event": data.event_type}
