"""Проверка начисления баллов с учётом качества SQL."""

from collections.abc import Coroutine
from types import SimpleNamespace
from typing import Any

from src.repositories import task as task_repository_module
from src.repositories.task import TaskRepository


def resolve_immediate(coroutine: Coroutine[Any, Any, Any]) -> Any:
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError("Тестовая корутина неожиданно приостановила выполнение")


def test_correct_solution_receives_reduced_reward(monkeypatch) -> None:
    added_points: list[int] = []

    class FakeSession:
        async def commit(self) -> None:
            return None

    class FakeScoringService:
        def __init__(self, session) -> None:
            pass

        async def add_points(self, user_id: int, points: int) -> None:
            added_points.append(points)

    class FakeUserRepository:
        def __init__(self, session) -> None:
            pass

        async def get_user_by_id(self, user_id: int):
            return SimpleNamespace(total_score=50)

        async def get_user_progress_by_id(self, user_id: int):
            return None

    async def fake_get_task_data(self, mission_id: int, task_id: int):
        return 100, []

    async def fake_check_already_solved(self, user_id: int, task_id: int):
        return False

    async def fake_add_solved_task(self, user_id: int, task_id: int, user_query=None):
        return None

    monkeypatch.setattr(
        task_repository_module,
        "ScoringService",
        FakeScoringService,
    )
    monkeypatch.setattr(
        task_repository_module,
        "UserRepository",
        FakeUserRepository,
    )
    monkeypatch.setattr(TaskRepository, "_get_task_data", fake_get_task_data)
    monkeypatch.setattr(
        TaskRepository,
        "_check_already_solved",
        fake_check_already_solved,
    )
    monkeypatch.setattr(
        TaskRepository,
        "add_solved_task",
        fake_add_solved_task,
    )

    repository = TaskRepository(FakeSession())
    result = resolve_immediate(repository.check_and_reward_task(
        user_id=1,
        mission_id=0,
        task_id=1,
        is_correct=True,
        quality_penalty=20,
    ))

    assert added_points == [80]
    assert result["points_earned"] == 80
    assert result["points_penalty"] == 20
    assert result["current_points"] == 130
    assert "качество SQL" in result["message"]
