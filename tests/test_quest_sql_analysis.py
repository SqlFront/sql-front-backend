"""Проверки подключения AST-анализа к SQL-квестам."""

from collections.abc import Coroutine
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from src.api import quests as quest_api
from src.schemas.quest import QuestRunRequest, QuestSubmitRequest
from src.sql_analysis import SUBMIT_SELECT_POLICY, UPDATE_POLICY, SQLAnalyzer
from src.sql_validation import configure_analysis
from src.utils.quest_loader import QuestLoader


def resolve_immediate(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """Завершает корутину без реального асинхронного ввода-вывода."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()

    raise AssertionError("Тестовая корутина неожиданно приостановила выполнение")


class FakeQuestRepository:
    async def get_user_current_scene(self, user_id: int, quest_id: str) -> dict:
        return {
            "scene_id": "scene-1",
            "is_branching": False,
        }


class FakeQuestExecutor:
    def __init__(self, affected_rows: int = 1) -> None:
        self.executed_queries: list[str] = []
        self.affected_rows = affected_rows

    async def execute_analyzed_sql(self, sql_query: str) -> dict:
        self.executed_queries.append(sql_query)
        return {
            "columns": ["id"],
            "data": [[1]],
            "row_count": 1,
        }

    async def simulate_analyzed_updates(
        self,
        sql_queries: tuple[str, ...],
        verification_query: str | None = None,
    ) -> dict:
        self.executed_queries.extend(sql_queries)
        if verification_query:
            return {
                "columns": ["update_correct"],
                "data": [[True]],
                "row_count": 1,
                "affected_rows": 3,
            }
        return {
            "columns": [],
            "data": [],
            "row_count": self.affected_rows,
            "affected_rows": self.affected_rows,
        }


def test_quest_run_uses_preview_policy(monkeypatch) -> None:
    executor = FakeQuestExecutor()
    monkeypatch.setattr(quest_api, "sql_executor", executor)

    response = resolve_immediate(quest_api.run_quest_sql(
        quest_id="hope",
        request=QuestRunRequest(
            scene_id="scene-1",
            sql_query="SELECT * FROM map",
        ),
        current_user=SimpleNamespace(user_id=1),
        repo=FakeQuestRepository(),
    ))

    assert response["data"] == [[1]]
    assert executor.executed_queries == ["SELECT * FROM map"]

    executor.executed_queries.clear()
    with pytest.raises(HTTPException) as rejected:
        resolve_immediate(quest_api.run_quest_sql(
            quest_id="hope",
            request=QuestRunRequest(
                scene_id="scene-1",
                sql_query="DELETE FROM map",
            ),
            current_user=SimpleNamespace(user_id=1),
            repo=FakeQuestRepository(),
        ))

    assert rejected.value.detail["message"] == "SQL-запрос заблокирован анализатором"
    assert rejected.value.detail["analysis"]["summary"]["blocking_issue_count"] == 1

    assert executor.executed_queries == []


def test_update_policy_limits_target_table_and_extracts_ast_value() -> None:
    analyzer = SQLAnalyzer()
    policy = replace(
        UPDATE_POLICY,
        allowed_tables=frozenset({"decision"}),
    )

    allowed = analyzer.analyze(
        "UPDATE decision SET result = '2' WHERE id = 1",
        policy,
    )
    forbidden = analyzer.analyze(
        "UPDATE secret_decision SET result = 2",
        policy,
    )

    assert allowed.can_execute is True
    assert allowed.parsed_query is not None
    assert quest_api._extract_update_value(
        allowed.parsed_query,
        "result",
    ) == "2"
    assert forbidden.can_execute is False
    assert [finding.code for finding in forbidden.findings] == [
        "security.table_not_allowed",
    ]


class FakeBranchingQuestRepository:
    async def get_user_current_scene(self, user_id: int, quest_id: str) -> dict:
        return {
            "scene_id": "chapter_4",
            "task": "Выберите ветку",
            "tags": ["update", "branching"],
            "is_branching": True,
            "branches": {"1": "factory", "2": "bridge"},
            "expected_result": {
                "query_type": "UPDATE",
                "target_table": "decision",
                "target_column": "result",
                "analysis_context": {
                    "schema": {"decision": ["result"]},
                    "strict_schema": True,
                },
                "analysis_requirements": {
                    "required_tables": ["decision"],
                },
            },
        }

    async def is_task_solved(self, user_id: int, quest_id: str, scene_id: str) -> bool:
        return False

    async def submit_answer(self, **kwargs) -> dict:
        return {"status": "in_progress"}

    async def mark_task_solved(self, *args) -> None:
        return None


def test_branching_update_can_be_previewed_safely(monkeypatch) -> None:
    executor = FakeQuestExecutor()
    monkeypatch.setattr(quest_api, "sql_executor", executor)

    response = resolve_immediate(quest_api.run_quest_sql(
        quest_id="hope",
        request=QuestRunRequest(
            scene_id="chapter_4",
            sql_query="UPDATE decision SET result = 2",
        ),
        current_user=SimpleNamespace(user_id=1),
        repo=FakeBranchingQuestRepository(),
    ))

    assert response["affected_rows"] == 1
    assert response["analysis"]["summary"]["blocking_issue_count"] == 0
    assert executor.executed_queries == ["UPDATE decision SET result = 2"]


class FakeUpdateSubmitRepository:
    def __init__(self) -> None:
        self.marked_solved = False

    async def get_user_current_scene(self, user_id: int, quest_id: str) -> dict:
        return {
            "scene_id": "chapter_5_2_2",
            "task": "Повредите три сегмента",
            "tags": ["update", "where", "between"],
            "is_branching": False,
            "expected_result": {
                "query_type": "UPDATE",
                "target_table": "track_segments",
                "target_column": "status",
                "verification_query": "SELECT true AS update_correct",
                "verification_result": {
                    "columns": ["update_correct"],
                    "data": [[True]],
                    "row_count": 1,
                },
                "analysis_context": {
                    "schema": {
                        "track_segments": [
                            "segment_id", "bridge", "km_marker", "status"
                        ],
                    },
                    "strict_schema": True,
                },
                "analysis_requirements": {
                    "required_tables": ["track_segments"],
                },
            },
        }

    async def is_task_solved(self, user_id: int, quest_id: str, scene_id: str) -> bool:
        return False

    async def submit_answer(self, **kwargs) -> dict:
        return {"status": "in_progress"}

    async def mark_task_solved(self, *args) -> None:
        self.marked_solved = True


class FakeScoringService:
    async def add_points(self, user_id: int, points: int) -> None:
        return None

    async def deduct_points(self, user_id: int, points: int) -> None:
        return None


class FakeDatabaseSession:
    def add(self, value) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def test_non_branching_update_is_verified_before_acceptance(monkeypatch) -> None:
    executor = FakeQuestExecutor()
    repository = FakeUpdateSubmitRepository()
    monkeypatch.setattr(quest_api, "sql_executor", executor)
    monkeypatch.setattr(
        quest_api,
        "ScoringService",
        lambda db: FakeScoringService(),
    )

    response = resolve_immediate(quest_api.submit_quest_solution(
        quest_id="hope",
        request=QuestSubmitRequest(
            scene_id="chapter_5_2_2",
            sql_query=(
                "UPDATE track_segments SET status = 'damaged' "
                "WHERE bridge = 'NorthBridge' AND km_marker BETWEEN 120 AND 122"
            ),
        ),
        current_user=SimpleNamespace(user_id=1),
        repo=repository,
        db=FakeDatabaseSession(),
    ))

    assert response["is_correct"] is True
    assert response["analysis"]["summary"]["blocking_issue_count"] == 0
    assert repository.marked_solved is True
    assert executor.executed_queries == [
        "UPDATE track_segments SET status = 'damaged' "
        "WHERE bridge = 'NorthBridge' AND km_marker BETWEEN 120 AND 122"
    ]


def test_branching_update_must_actually_change_the_choice(monkeypatch) -> None:
    executor = FakeQuestExecutor(affected_rows=0)
    monkeypatch.setattr(quest_api, "sql_executor", executor)
    monkeypatch.setattr(
        quest_api,
        "ScoringService",
        lambda db: FakeScoringService(),
    )

    response = resolve_immediate(quest_api.submit_quest_solution(
        quest_id="hope",
        request=QuestSubmitRequest(
            scene_id="chapter_4",
            sql_query="UPDATE decision SET result = 2 WHERE 1 = 0",
        ),
        current_user=SimpleNamespace(user_id=1),
        repo=FakeBranchingQuestRepository(),
        db=FakeDatabaseSession(),
    ))

    assert response["is_correct"] is False
    assert response["feedback"] == [
        "Запрос не изменил выбор или указал недопустимое значение"
    ]


def test_quest_loader_merges_analysis_config_without_mutating_story() -> None:
    QuestLoader._cache.clear()
    QuestLoader._analysis_cache.clear()

    raw_scene = QuestLoader.get_quest("hope")["scenes"]["chapter_5_2_2"]
    configured_scene = QuestLoader.get_scene("hope", "chapter_5_2_2")

    assert "verification_query" not in raw_scene["expected_result"]
    assert configured_scene["expected_result"]["max_statement_count"] == 1
    assert configured_scene["expected_result"]["verification_result"]["data"] == [[True]]


@pytest.mark.parametrize(("scene_id", "sql"), [
    (
        "chapter_1",
        "SELECT id, name, description, coordinates FROM map WHERE status = 'military'",
    ),
    (
        "chapter_2",
        "SELECT m.id, m.name, m.description, m.coordinates, s.importance "
        "FROM map m JOIN is_sensitive s ON s.id = m.id "
        "ORDER BY s.importance DESC LIMIT 5",
    ),
    (
        "chapter_3",
        "SELECT m.id, m.name, c.description FROM map m "
        "JOIN critical_objects c ON c.id = m.id "
        "WHERE m.name IN ('Танковый завод', 'ЖД-мост')",
    ),
    ("chapter_4", "UPDATE decision SET result = 1"),
    ("chapter_5_1", "UPDATE decision_factory SET result = 10"),
    (
        "chapter_5_1_10_1",
        "SELECT s.shift_id, COUNT(g.guard_id) AS guard_count FROM shifts s "
        "JOIN guards g ON g.shift_id = s.shift_id "
        "WHERE s.status = 'active' AND s.start_time = '22:00' AND s.sector = 'D' "
        "GROUP BY s.shift_id",
    ),
    (
        "chapter_5_1_10_2",
        "SELECT e.item_id, e.name, e.weight FROM explosives e "
        "JOIN storages s ON s.storage_id = e.storage_id "
        "WHERE e.type = 'thermite' AND e.weight < 1.5 "
        "AND s.sector = 'D' AND s.security_level IN ('high', 'critical')",
    ),
    (
        "chapter_5_1_10_3",
        "SELECT r.route_id, r.start_sector, r.distance_km FROM routes r "
        "JOIN checkpoints c ON c.sector = r.start_sector "
        "WHERE r.end_sector = 'D' AND r.risk_level = 'low' "
        "AND c.status <> 'active' ORDER BY r.distance_km LIMIT 1",
    ),
    (
        "chapter_5_1_10_5",
        "SELECT t.template_id, t.name, d.activation_date FROM disguise_templates t "
        "JOIN disguises d ON d.template_id = t.template_id "
        "WHERE t.origin_country = 'Germany' AND t.uniform_type ILIKE '%officer%' "
        "AND d.status = 'approved'",
    ),
    (
        "chapter_5_1_20_1",
        "UPDATE items SET assigned_to = 'Sasha' WHERE weight <= 2; "
        "UPDATE items SET assigned_to = 'Grisha' WHERE weight > 2",
    ),
    (
        "chapter_5_2_1",
        "SELECT train_id, arrival_time FROM train_schedule "
        "WHERE cargo_type = 'tanks' AND arrival_time > '1944-09-19 06:00' "
        "ORDER BY arrival_time LIMIT 1",
    ),
    (
        "chapter_5_2_2",
        "UPDATE track_segments SET status = 'damaged' "
        "WHERE bridge = 'NorthBridge' AND km_marker BETWEEN 120 AND 122",
    ),
])
def test_reference_quest_solutions_satisfy_scene_analysis(scene_id, sql) -> None:
    scene = QuestLoader.get_scene("hope", scene_id)
    base_policy = UPDATE_POLICY if quest_api._is_update_scene(scene) else SUBMIT_SELECT_POLICY
    if quest_api._is_update_scene(scene):
        policy, _ = quest_api._configure_update_scene(scene)
    else:
        policy, _ = configure_analysis(
            base_policy,
            question=scene.get("task") or "",
            expected_result=scene.get("expected_result"),
            tags=scene.get("tags"),
        )

    analysis = SQLAnalyzer().analyze(sql, policy)

    assert analysis.can_execute is True, [
        (finding.code, finding.message) for finding in analysis.findings
    ]
