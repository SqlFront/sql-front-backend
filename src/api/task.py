import logging
import re
from collections.abc import Mapping

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
    DatabaseSchemaResponse,
)

from src.utils.schema_inspector import schema_inspector
from src.utils.analytics import log_user_event
from src.utils.auth import get_current_user
from src.utils.sql_executor import SQLExecutor
from src.utils import catalog_model
import logging
import re

from src.sql_analysis import (
    PREVIEW_SELECT_POLICY,
    SUBMIT_SELECT_POLICY,
    PostgresDDLAnalyzer,
    SQLAnalyzer,
)
from src.sql_validation import (
    ComparisonPolicy,
    QueryResult,
    ResultComparator,
    SQLValidationService,
    ValidationRequest,
    assess_query_quality,
    build_analysis_error_detail,
    build_analysis_payload,
    build_findings_payload,
    configure_analysis,
)
from src.utils import catalog_model
from src.utils.analytics import log_user_event
from src.utils.auth import get_current_user
from src.utils.sql_executor import SQLExecutor

logger = logging.getLogger("api.task")

router = APIRouter(prefix="/api/missions", tags=["Миссии и задачи"])
sql_executor = SQLExecutor(settings.GAME_DATABASE_URL)
sql_result_comparator = ResultComparator()
sql_analyzer = SQLAnalyzer()
ddl_analyzer = PostgresDDLAnalyzer()
sql_validation_service = SQLValidationService(
    analyzer=sql_analyzer,
    executor=sql_executor,
    comparator=sql_result_comparator,
)
SUBMIT_COMPARISON_POLICY = ComparisonPolicy(
    compare_columns=True,
    row_order_matters=False,
)


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
    "/schema",
    summary="Динамическая схема базы данных (ER-диаграмма)",
    description="Возвращает актуальный граф таблиц, колонок и связей из системного каталога PostgreSQL для отображения в ER-диаграмме",
    response_model=DatabaseSchemaResponse,
)
async def get_database_schema(refresh: bool = False):
    try:
        return await schema_inspector.get_schema(refresh=refresh)
    except Exception as e:
        logger.error(f"Error fetching database schema: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить схему базы данных")

def _ddl_verification_cases(
        expected_result: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    """Возвращает новые verification_cases или один legacy test_query."""
    configured = expected_result.get("verification_cases")
    if isinstance(configured, list):
        cases = tuple(case for case in configured if isinstance(case, Mapping))
        if cases:
            return cases
    return (expected_result,)


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
    task, is_solved, user_solution = await repo.get_task_info_with_status(
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
        "user_solution": user_solution,
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
        sql_query = (request.sql_query or "").strip()
        if not sql_query:
            raise HTTPException(status_code=400, detail="Пустой запрос")

        exp_res = task.expected_result or {}

        preview_policy, quality_policy = configure_analysis(
            PREVIEW_SELECT_POLICY,
            question=getattr(task, "description", ""),
            expected_result=exp_res,
            tags=getattr(task, "tags", None),
        )
        if exp_res.get("mode") == "model":
            if re.search(r"\b(?:DROP\s+DATABASE|ALTER\s+SYSTEM)\b", sql_query, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="DROP DATABASE / ALTER SYSTEM запрещены",
                )
            model = catalog_model.Model(exp_res.get("database", "quest_sandbox"))
            try:
                for statement in exp_res.get("setup", []):
                    model.execute(statement)
                model.execute(sql_query)
            except catalog_model.ModelError as exc:
                raise HTTPException(status_code=400, detail=f"Ошибка выполнения: {exc}") from exc
            operation = SQLExecutor._extract_operation_type(sql_query)
            return {
                "columns": ["Статус операции"],
                "data": [[f"Команда успешно выполнена: {operation} (симуляция завершена успешно)"]],
                "row_count": 1,
                "analysis": build_findings_payload(
                    (),
                    preview_policy.task_context,
                    penalty_policy=quality_policy,
                ),
            }
        elif exp_res.get("mode") in ("ddl", "plpgsql"):
            ddl_analysis = ddl_analyzer.analyze(request.sql_query)
            if not ddl_analysis.can_execute:
                raise HTTPException(
                    status_code=400,
                    detail=build_analysis_error_detail(
                        "DDL-запрос заблокирован анализатором",
                        ddl_analysis.findings,
                        preview_policy.task_context,
                        penalty_policy=quality_policy,
                    ),
                )
            preview_case = _ddl_verification_cases(exp_res)[0]
            result = dict(await sql_executor.simulate_analyzed_ddl(
                request.sql_query,
                preview_case.get("test_query", ""),
                expect_error=bool(preview_case.get("expect_error", False)),
            ))
            result["analysis"] = build_findings_payload(
                ddl_analysis.findings,
                preview_policy.task_context,
                penalty_policy=quality_policy,
            )
            return result
        analysis = sql_analyzer.analyze(request.sql_query, preview_policy)
        if not analysis.can_execute:
            raise HTTPException(
                status_code=400,
                detail=build_analysis_error_detail(
                    "SQL-запрос заблокирован анализатором",
                    analysis.findings,
                    preview_policy.task_context,
                    penalty_policy=quality_policy,
                ),
            )

        result = dict(await sql_executor.execute_analyzed_sql(request.sql_query))
        result["analysis"] = build_analysis_payload(
            analysis,
            preview_policy.task_context,
            penalty_policy=quality_policy,
        )
        return result
    except HTTPException:
        raise
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
    quality_issues: list[str] = []
    quality_penalty = 0
    analysis_payload = None
    user_result = {}
    submit_policy, quality_policy = configure_analysis(
        SUBMIT_SELECT_POLICY,
        question=getattr(task, "description", ""),
        expected_result=expected_result,
        tags=getattr(task, "tags", None),
    )
    try:
        if expected_result.get("mode") == "model":
            is_correct, hint = catalog_model.verify(request.sql_query, expected_result)

            quality_assessment = (
                assess_query_quality(
                    (), settings.TASK_POINTS[mission_id], policy=quality_policy
                )
                if is_correct else None
            )
            analysis_payload = build_findings_payload(
                (),
                submit_policy.task_context,
                penalty_policy=quality_policy,
                quality=quality_assessment,
            )
        elif expected_result.get("mode") in ("ddl", "plpgsql"):
            ddl_analysis = ddl_analyzer.analyze(request.sql_query)
            if not ddl_analysis.can_execute:
                is_correct = False
                hint = "; ".join(
                    finding.message for finding in ddl_analysis.findings
                )
            else:
                is_correct = True
                for case_number, verification_case in enumerate(
                        _ddl_verification_cases(expected_result),
                        start=1,
                ):
                    user_result = await sql_executor.simulate_analyzed_ddl(
                        request.sql_query,
                        verification_case.get("test_query", ""),
                        expect_error=bool(
                            verification_case.get("expect_error", False)
                        ),
                    )
                    if verification_case.get("expect_error", False):
                        case_is_correct = user_result.get("error_caught", False)
                        case_hint = (
                            "Триггер успешно заблокировал некорректную операцию"
                            if case_is_correct else "Ожидаемая ошибка не возникла"
                        )
                    else:
                        comparison = sql_result_comparator.compare(
                            actual=QueryResult.from_mapping(user_result),
                            expected=QueryResult.from_mapping(verification_case),
                            policy=ComparisonPolicy(compare_columns=False),
                        )
                        case_is_correct = comparison.is_equal
                        case_hint = "; ".join(
                            difference.message
                            for difference in comparison.differences
                        )
                    if not case_is_correct:
                        is_correct = False
                        hint = f"Проверочный вызов {case_number}: {case_hint}"
                        break
                    hint = case_hint
            quality_assessment = (
                assess_query_quality(
                    ddl_analysis.findings,
                    settings.TASK_POINTS[mission_id],
                    policy=quality_policy,
                )
                if is_correct else None
            )
            if quality_assessment is not None:
                quality_penalty = quality_assessment.penalty_points
                quality_issues = list(quality_assessment.messages)
                if quality_issues:
                    hint = "; ".join(quality_issues)
            analysis_payload = build_findings_payload(
                ddl_analysis.findings,
                submit_policy.task_context,
                penalty_policy=quality_policy,
                quality=quality_assessment,
            )
        else:
            validation = await sql_validation_service.validate(
                ValidationRequest(
                    sql=request.sql_query,
                    analysis_policy=submit_policy,
                    expected_result=QueryResult.from_mapping(expected_result),
                    comparison_policy=SUBMIT_COMPARISON_POLICY,
                )
            )
            is_correct = validation.is_correct

            quality_assessment = None
            if is_correct:
                quality_assessment = assess_query_quality(
                    validation.analysis.findings,
                    settings.TASK_POINTS[mission_id],
                    policy=quality_policy,
                )
                quality_issues = list(quality_assessment.messages)
                quality_penalty = quality_assessment.penalty_points

            analysis_payload = build_analysis_payload(
                validation.analysis,
                submit_policy.task_context,
                penalty_policy=quality_policy,
                quality=quality_assessment,
            )

            if validation.execution is not None:
                user_result = {
                    "columns": list(validation.execution.columns),
                    "data": [list(row) for row in validation.execution.rows],
                    "row_count": validation.execution.row_count,
                }

            if quality_issues:
                hint = "; ".join(quality_issues)
            elif not is_correct:
                hint = "; ".join(validation.feedback)
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
            quality_penalty=quality_penalty if is_correct else 0,
            user_query=request.sql_query if is_correct else None,
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
            "quality_issues": quality_issues,
            "analysis": analysis_payload,
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
