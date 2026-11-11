"""Проверки сравнения результатов и полного сервиса валидации."""

from collections.abc import Coroutine
from types import SimpleNamespace
from typing import Any

import pytest

from src.sql_analysis import AnalysisPolicy, SQLAnalyzer, SUBMIT_SELECT_POLICY
from src.sql_validation import (
    ComparisonPolicy,
    QueryResult,
    ResultComparator,
    SQLValidationService,
    ValidationRequest,
    VerdictStatus,
    QualityPenaltyPolicy,
    assess_query_quality,
    build_analysis_payload,
    configure_analysis,
)
from src.sql_analysis import TaskAnalysisContext


def make_result(columns: tuple[str, ...], rows: tuple[tuple, ...]) -> QueryResult:
    return QueryResult(columns=columns, rows=rows, row_count=len(rows))


def resolve_immediate(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """Завершает корутину, которая не выполняет реального ввода-вывода."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()

    raise AssertionError("Тестовая корутина неожиданно приостановила выполнение")


def test_comparator_ignores_row_order_and_preserves_duplicates() -> None:
    comparator = ResultComparator()
    actual = make_result(("value",), ((None,), (1,), (1,)))
    expected = make_result(("value",), ((1,), (None,), (1,)))

    result = comparator.compare(actual, expected, ComparisonPolicy())

    assert result.is_equal is True
    assert result.differences == ()


def test_comparator_can_require_row_order() -> None:
    comparator = ResultComparator()
    actual = make_result(("value",), ((1,), (2,)))
    expected = make_result(("value",), ((2,), (1,)))

    result = comparator.compare(
        actual,
        expected,
        ComparisonPolicy(row_order_matters=True),
    )

    assert result.is_equal is False
    assert result.rows_equal is False


def test_comparator_detects_column_difference() -> None:
    comparator = ResultComparator()
    actual = make_result(("actual_name",), ((1,),))
    expected = make_result(("expected_name",), ((1,),))

    result = comparator.compare(actual, expected, ComparisonPolicy())

    assert result.is_equal is False
    assert result.columns_equal is False
    assert result.differences[0].code == "columns_mismatch"


def test_comparator_uses_float_tolerance() -> None:
    comparator = ResultComparator()
    actual = make_result(("value",), ((1.001,),))
    expected = make_result(("value",), ((1.0,),))

    result = comparator.compare(
        actual,
        expected,
        ComparisonPolicy(float_tolerance=0.01),
    )

    assert result.is_equal is True


def test_comparator_detects_row_count_for_results_without_rows() -> None:
    comparator = ResultComparator()
    actual = QueryResult(columns=(), rows=(), row_count=2)
    expected = QueryResult(columns=(), rows=(), row_count=1)

    result = comparator.compare(actual, expected, ComparisonPolicy())

    assert result.is_equal is False
    assert result.differences[0].code == "row_count_mismatch"


def test_quality_assessment_reduces_points_for_style_warnings() -> None:
    analysis = SQLAnalyzer().analyze(
        "SELECT id FROM users, orders WHERE users.id = orders.user_id ORDER BY 1",
        AnalysisPolicy(allowed_statement_types=frozenset({"select"})),
    )

    quality = assess_query_quality(analysis.findings, available_points=100)

    assert quality.penalty_points == 20
    assert quality.penalty_rate == pytest.approx(0.20)
    assert len(quality.messages) == 3
    assert quality.grade.value == "good"
    assert quality.score_percent == 80


def test_quality_policy_can_be_configured_per_task() -> None:
    analysis = SQLAnalyzer().analyze(
        "SELECT id FROM users, orders WHERE users.id = orders.user_id ORDER BY 1",
        AnalysisPolicy(allowed_statement_types=frozenset({"select"})),
    )
    policy = QualityPenaltyPolicy.from_mapping({
        "penalty_rates": {
            "style.implicit_join": 0.20,
            "style.unqualified_columns": 0.10,
            "style.order_by_ordinal": 0.10,
        },
        "max_penalty_rate": 0.25,
        "grade_thresholds": {"good": 0.80, "excellent": 0.95},
    })

    quality = assess_query_quality(
        analysis.findings,
        available_points=200,
        policy=policy,
    )

    assert quality.penalty_points == 50
    assert quality.awarded_points == 150
    assert quality.grade.value == "satisfactory"


def test_analysis_payload_contains_question_schema_and_locations() -> None:
    context = TaskAnalysisContext(
        question="Выведите идентификаторы",
        difficulty="easy",
        schema={"users": ("id",)},
        strict_schema=True,
    )
    analysis = SQLAnalyzer().analyze(
        "SELECT * FROM users",
        AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
            task_context=context,
        ),
    )

    payload = build_analysis_payload(analysis, context)

    assert payload["context"]["question"] == "Выведите идентификаторы"
    assert payload["context"]["schema"] == {"users": ["id"]}
    assert payload["summary"]["issue_count"] == 1
    assert payload["findings"][0]["location"]["column"] == 8


def test_task_configuration_combines_question_schema_requirements_and_quality() -> None:
    policy, quality_policy = configure_analysis(
        AnalysisPolicy(allowed_statement_types=frozenset({"select"})),
        question="Сгруппируйте заказы",
        tags=["hard", "group_by"],
        expected_result={
            "analysis_requirements": {"required_tables": ["orders"]},
            "analysis_context": {
                "schema": {"orders": ["id", "total"]},
                "strict_schema": True,
            },
            "quality_policy": {
                "penalty_rates": {"style.order_by_ordinal": 0.12},
                "max_penalty_rate": 0.40,
            },
        },
    )

    assert policy.task_context.question == "Сгруппируйте заказы"
    assert policy.task_context.difficulty == "hard"
    assert policy.task_context.schema == {"orders": ("id", "total")}
    assert policy.requirements.required_tables == frozenset({"orders"})
    assert "group_by" in policy.requirements.required_features
    assert quality_policy.penalty_rates["style.order_by_ordinal"] == 0.12
    assert quality_policy.max_penalty_rate == 0.40


def test_task_configuration_resolves_catalog_tables_and_can_ignore_tags() -> None:
    policy, _ = configure_analysis(
        SUBMIT_SELECT_POLICY,
        question="Сгруппируйте снаряжение по типу",
        expected_result={
            "analysis_tables": ["equipment"],
            "derive_requirements_from_tags": False,
            "analysis_context": {"strict_schema": True},
            "analysis_requirements": {
                "required_tables": ["equipment"],
                "required_features": ["group_by", "aggregate_function"],
            },
        },
        tags=["window", "easy"],
    )

    assert policy.task_context.strict_schema is True
    assert policy.task_context.schema["equipment"] == (
        "id",
        "unit_id",
        "equipment_type",
        "item_name",
        "quantity",
        "last_replenishment",
    )
    assert policy.requirements.required_features == frozenset({
        "group_by",
        "aggregate_function",
    })

    analysis = SQLAnalyzer().analyze(
        "SELECT equipment_type, SUM(quantity) AS total "
        "FROM equipment GROUP BY equipment_type",
        policy,
    )
    assert analysis.can_execute is True
    assert "window_function" not in policy.requirements.required_features


class FakeExecutor:
    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self.result = result or {"columns": [], "data": [], "row_count": 0}
        self.error = error
        self.calls: list[str] = []

    async def execute_analyzed_sql(self, sql_query: str) -> dict:
        self.calls.append(sql_query)
        if self.error is not None:
            raise self.error
        return self.result


def make_request(sql: str) -> ValidationRequest:
    return ValidationRequest(
        sql=sql,
        analysis_policy=AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
        ),
        expected_result=make_result(("id",), ((1,),)),
    )


def test_service_returns_correct_verdict() -> None:
    executor = FakeExecutor({
        "columns": ["id"],
        "data": [[1]],
        "row_count": 1,
    })
    service = SQLValidationService(SQLAnalyzer(), executor)

    result = resolve_immediate(
        service.validate(make_request("SELECT id FROM items"))
    )

    assert result.status == VerdictStatus.CORRECT
    assert result.is_correct is True
    assert executor.calls == ["SELECT id FROM items"]


def test_service_does_not_execute_rejected_sql() -> None:
    executor = FakeExecutor()
    service = SQLValidationService(SQLAnalyzer(), executor)

    result = resolve_immediate(
        service.validate(make_request("DELETE FROM items"))
    )

    assert result.status == VerdictStatus.REJECTED
    assert result.execution is None
    assert executor.calls == []


def test_service_distinguishes_invalid_sql() -> None:
    executor = FakeExecutor()
    service = SQLValidationService(SQLAnalyzer(), executor)

    result = resolve_immediate(service.validate(make_request("SELECT (")))

    assert result.status == VerdictStatus.INVALID_SQL
    assert executor.calls == []


def test_service_converts_execution_error_to_verdict() -> None:
    executor = FakeExecutor(error=RuntimeError("database unavailable"))
    service = SQLValidationService(SQLAnalyzer(), executor)

    result = resolve_immediate(
        service.validate(make_request("SELECT id FROM items"))
    )

    assert result.status == VerdictStatus.RUNTIME_ERROR
    assert result.feedback == ("database unavailable",)


def test_task_submit_uses_validation_service(monkeypatch) -> None:
    from src.api import task as task_api
    from src.schemas.task import SQLRequest

    executor = FakeExecutor({
        "columns": ["wrong_alias"],
        "data": [[1]],
        "row_count": 1,
    })
    validation_service = SQLValidationService(SQLAnalyzer(), executor)

    class FakeTaskRepository:
        submitted_is_correct: bool | None = None

        async def get_task_info(self, mission_id: int, task_id: int):
            return SimpleNamespace(
                task_global_id=10,
                expected_result={
                    "columns": ["id"],
                    "data": [[1]],
                    "row_count": 1,
                },
            )

        async def check_and_reward_task(
                self,
                user_id: int,
                mission_id: int,
                task_id: int,
                is_correct: bool,
                quality_penalty: int = 0,
                user_query: str | None = None,
        ) -> dict:
            self.submitted_is_correct = is_correct
            return {
                "was_solved_before": False,
                "points_earned": 0,
                "points_penalty": 0,
                "message": "Ответ неверный!",
                "awarded_achievements": [],
                "current_points": 0,
            }

    async def fake_log_user_event(**kwargs) -> None:
        return None

    repository = FakeTaskRepository()
    monkeypatch.setattr(
        task_api,
        "sql_validation_service",
        validation_service,
    )
    monkeypatch.setattr(task_api, "log_user_event", fake_log_user_event)
    monkeypatch.setattr(task_api, "TaskRepository", lambda db: repository)

    response = resolve_immediate(task_api.submit_sql_query(
        mission_id=0,
        task_id=1,
        request=SQLRequest(sql_query="SELECT id FROM items"),
        current_user=SimpleNamespace(user_id=1),
        db=object(),
    ))

    assert repository.submitted_is_correct is False
    assert response["is_correct"] is False
    assert response["columns"] == ["wrong_alias"]
    assert response["data"] == [[1]]
    assert "столбцов" in response["hint"]
    assert response["analysis"]["summary"]["issue_count"] == 0
    assert response["analysis"]["context"]["difficulty"] == "medium"


def test_task_run_uses_preview_analysis(monkeypatch) -> None:
    from fastapi import HTTPException

    from src.api import task as task_api
    from src.schemas.task import SQLRequest

    executor = FakeExecutor({
        "columns": ["id"],
        "data": [[1]],
        "row_count": 1,
    })

    class FakeTaskRepository:
        async def get_task_info(self, mission_id: int, task_id: int):
            return SimpleNamespace(task_global_id=10, expected_result={})

    async def fake_log_user_event(**kwargs) -> None:
        return None

    monkeypatch.setattr(task_api, "sql_executor", executor)
    monkeypatch.setattr(task_api, "log_user_event", fake_log_user_event)
    monkeypatch.setattr(
        task_api,
        "TaskRepository",
        lambda db: FakeTaskRepository(),
    )

    response = resolve_immediate(task_api.run_sql_query(
        mission_id=0,
        task_id=1,
        request=SQLRequest(sql_query="SELECT * FROM items"),
        current_user=SimpleNamespace(user_id=1),
        db=object(),
    ))

    assert response["data"] == [[1]]
    assert response["analysis"]["summary"]["issue_count"] == 0
    assert executor.calls == ["SELECT * FROM items"]

    executor.calls.clear()
    with pytest.raises(HTTPException) as rejected:
        resolve_immediate(task_api.run_sql_query(
            mission_id=0,
            task_id=1,
            request=SQLRequest(sql_query="DELETE FROM items"),
            current_user=SimpleNamespace(user_id=1),
            db=object(),
        ))

    assert executor.calls == []
    assert rejected.value.detail["message"] == "SQL-запрос заблокирован анализатором"
    assert rejected.value.detail["analysis"]["summary"]["blocking_issue_count"] == 1
    assert (
        rejected.value.detail["analysis"]["findings"][0]["code"]
        == "security.statement_type_forbidden"
    )
    assert "Runtime error" not in str(rejected.value.detail)


def test_ddl_submit_checks_every_configured_input(monkeypatch) -> None:
    from src.api import task as task_api
    from src.schemas.task import SQLRequest

    class FakeDDLExecutor:
        calls: list[str] = []

        async def simulate_analyzed_ddl(
                self,
                ddl_query: str,
                test_query: str,
                expect_error: bool = False,
        ) -> dict:
            self.calls.append(test_query)
            value_by_query = {
                "SELECT get_enlistment_age(1);": 18,
                "SELECT get_enlistment_age(2);": 18,
            }
            return {
                "columns": ["get_enlistment_age"],
                "data": [[value_by_query[test_query]]],
                "row_count": 1,
            }

    class FakeDDLRepository:
        async def get_task_info(self, mission_id: int, task_id: int):
            return SimpleNamespace(
                task_global_id=106,
                description="Вычислите возраст по идентификатору",
                tags=["plpgsql", "function", "hard"],
                expected_result={
                    "mode": "ddl",
                    "verification_cases": [
                        {
                            "test_query": "SELECT get_enlistment_age(1);",
                            "columns": ["get_enlistment_age"],
                            "data": [[18]],
                            "row_count": 1,
                        },
                        {
                            "test_query": "SELECT get_enlistment_age(2);",
                            "columns": ["get_enlistment_age"],
                            "data": [[17]],
                            "row_count": 1,
                        },
                    ],
                },
            )

        async def check_and_reward_task(self, **kwargs) -> dict:
            return {
                "was_solved_before": False,
                "points_earned": 0,
                "points_penalty": 0,
                "message": "Ответ неверный!",
                "awarded_achievements": [],
                "current_points": 0,
            }

    async def fake_log_user_event(**kwargs) -> None:
        return None

    executor = FakeDDLExecutor()
    monkeypatch.setattr(task_api, "sql_executor", executor)
    monkeypatch.setattr(task_api, "log_user_event", fake_log_user_event)
    monkeypatch.setattr(task_api, "TaskRepository", lambda db: FakeDDLRepository())

    response = resolve_immediate(task_api.submit_sql_query(
        mission_id=5,
        task_id=1,
        request=SQLRequest(sql_query="""
            CREATE FUNCTION get_enlistment_age(p_soldier_id INT)
            RETURNS INT AS $$ BEGIN RETURN 18; END; $$ LANGUAGE plpgsql;
        """),
        current_user=SimpleNamespace(user_id=1),
        db=object(),
    ))

    assert executor.calls == [
        "SELECT get_enlistment_age(1);",
        "SELECT get_enlistment_age(2);",
    ]
    assert response["is_correct"] is False
    assert response["hint"].startswith("Проверочный вызов 2:")


def test_ddl_preview_returns_quality_findings(monkeypatch) -> None:
    from src.api import task as task_api
    from src.schemas.task import SQLRequest

    class FakeDDLExecutor:
        async def simulate_analyzed_ddl(
                self,
                ddl_query: str,
                test_query: str,
                expect_error: bool = False,
        ) -> dict:
            return {
                "columns": ["get_enlistment_age"],
                "data": [[18]],
                "row_count": 1,
            }

    class FakeDDLRepository:
        async def get_task_info(self, mission_id: int, task_id: int):
            return SimpleNamespace(
                task_global_id=106,
                description="Вычислите возраст по идентификатору",
                tags=["plpgsql", "function", "hard"],
                expected_result={
                    "mode": "ddl",
                    "test_query": "SELECT get_enlistment_age(1);",
                    "columns": ["get_enlistment_age"],
                    "data": [[18]],
                    "row_count": 1,
                },
            )

    async def fake_log_user_event(**kwargs) -> None:
        return None

    monkeypatch.setattr(task_api, "sql_executor", FakeDDLExecutor())
    monkeypatch.setattr(task_api, "log_user_event", fake_log_user_event)
    monkeypatch.setattr(task_api, "TaskRepository", lambda db: FakeDDLRepository())

    response = resolve_immediate(task_api.run_sql_query(
        mission_id=5,
        task_id=1,
        request=SQLRequest(sql_query="""
            CREATE FUNCTION get_enlistment_age(p_soldier_id INT)
            RETURNS INT AS $$ BEGIN RETURN 18; END; $$ LANGUAGE plpgsql;
        """),
        current_user=SimpleNamespace(user_id=1),
        db=object(),
    ))

    codes = {finding["code"] for finding in response["analysis"]["findings"]}
    assert response["data"] == [[18]]
    assert "style.ddl_unused_parameter" in codes
    assert "efficiency.ddl_constant_return" in codes
