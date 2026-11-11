from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import sqlglot.expressions as exp

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
from src.sql_analysis import (
    PREVIEW_SELECT_POLICY,
    SUBMIT_SELECT_POLICY,
    UPDATE_POLICY,
    SQLAnalyzer,
)
from src.sql_analysis.parser import ParsedQuery
from src.sql_validation import (
    ComparisonPolicy,
    QueryResult,
    ResultComparator,
    SQLValidationService,
    ValidationRequest,
    assess_query_quality,
    build_analysis_error_detail,
    build_analysis_payload,
    configure_analysis,
)
from src.utils.auth import get_current_user
from src.utils.sql_executor import SQLExecutor
from src.utils.quest_loader import QuestLoader
from src.utils.scoring_service import ScoringService

router = APIRouter(prefix="/api/quests", tags=["Квесты"])
sql_executor = SQLExecutor(settings.QUEST_DATABASE_URL)
sql_analyzer = SQLAnalyzer()
sql_result_comparator = ResultComparator()
sql_validation_service = SQLValidationService(
    analyzer=sql_analyzer,
    executor=sql_executor,
    comparator=sql_result_comparator,
)
QUEST_COMPARISON_POLICY = ComparisonPolicy(
    compare_columns=True,
    row_order_matters=False,
)


def get_quest_repository(db: AsyncSession = Depends(get_db)) -> QuestRepository:
    return QuestRepository(db)



def sanitize_quest_query(query: str) -> str:
    """Нормализация и очистка SQL-запроса перед валидацией и выполнением.
    Удаляет хвостовые точки с запятой, пробелы, символы табуляции и переводы строк.
    """
    if not query:
        return ""
    cleaned = query.strip()
    while cleaned and (
        cleaned.endswith(";")
        or cleaned.endswith(" ")
        or cleaned.endswith("\n")
        or cleaned.endswith("\r")
        or cleaned.endswith("\t")
    ):
        cleaned = cleaned.rstrip("; \n\r\t").strip()
    return cleaned



def _extract_update_value(
        parsed_query: ParsedQuery,
        target_column: str | None,
) -> str:
    """Извлекает присваиваемое значение целевого столбца из UPDATE AST."""
    for statement in parsed_query.statements:
        if not isinstance(statement, exp.Update):
            continue

        for assignment in statement.expressions:
            if not isinstance(assignment, exp.EQ):
                continue
            if (
                target_column is not None
                and assignment.left.name.casefold() != target_column.casefold()
            ):
                continue

            if isinstance(assignment.right, exp.Literal):
                return str(assignment.right.this)
            return assignment.right.sql(dialect="postgres")

    return ""


def _is_update_scene(scene: dict) -> bool:
    """Определяет режим проверки по конфигурации сцены, а не по ветвлению."""
    expected_result = scene.get("expected_result") or {}
    query_type = str(expected_result.get("query_type", "")).casefold()
    tags = {str(tag).casefold() for tag in scene.get("tags") or ()}
    return query_type == "update" or "update" in tags


def _configure_update_scene(scene: dict):
    """Создаёт ограниченную политику UPDATE для конкретной сцены."""
    expected_result = scene.get("expected_result") or {}
    target_table = expected_result.get("target_table")
    if not target_table:
        raise HTTPException(
            status_code=500,
            detail="Для UPDATE-сцены не настроена целевая таблица",
        )

    try:
        max_statement_count = int(expected_result.get("max_statement_count", 1))
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Некорректный лимит количества UPDATE-операторов",
        ) from error

    return configure_analysis(
        replace(
            UPDATE_POLICY,
            allowed_tables=frozenset({str(target_table)}),
            max_statement_count=max_statement_count,
        ),
        question=scene.get("task") or "",
        expected_result=expected_result,
        tags=scene.get("tags"),
    )


def _parsed_statements_sql(parsed_query: ParsedQuery) -> tuple[str, ...]:
    """Возвращает отдельные SQL-операторы из уже проверенного AST."""
    return tuple(
        statement.sql(dialect="postgres")
        for statement in parsed_query.statements
    )

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

        expected_result = scene_data.get("expected_result") or {}
        if _is_update_scene(scene_data):
            update_policy, quality_policy = _configure_update_scene(scene_data)
            analysis = sql_analyzer.analyze(request.sql_query, update_policy)
            if not analysis.can_execute or analysis.parsed_query is None:
                raise HTTPException(
                    status_code=400,
                    detail=build_analysis_error_detail(
                        "SQL-запрос заблокирован анализатором",
                        analysis.findings,
                        update_policy.task_context,
                        penalty_policy=quality_policy,
                    ),
                )

            result = dict(await sql_executor.simulate_analyzed_updates(
                _parsed_statements_sql(analysis.parsed_query)
            ))
            result["analysis"] = build_analysis_payload(
                analysis,
                update_policy.task_context,
                penalty_policy=quality_policy,
            )
            return result

        preview_policy, quality_policy = configure_analysis(
            PREVIEW_SELECT_POLICY,
            question=scene_data.get("task") or "",
            expected_result=expected_result,
            tags=scene_data.get("tags"),
        )
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

    cleaned_query = sanitize_quest_query(request.sql_query)
    user_answer_value = ""
    is_correct = False
    feedback: tuple[str, ...] = ()
    quality_penalty = 0
    analysis_payload = None

    try:

        if _is_update_scene(scene):
            expected_result = scene.get("expected_result") or {}
            target_column = expected_result.get("target_column")
            update_policy, quality_policy = _configure_update_scene(scene)
            analysis = sql_analyzer.analyze(request.sql_query, update_policy)
            quality_assessment = None

            if analysis.can_execute and analysis.parsed_query is not None:
                statements = _parsed_statements_sql(analysis.parsed_query)
                if scene["is_branching"]:
                    user_answer_value = _extract_update_value(
                        analysis.parsed_query,
                        target_column,
                    )
                    execution = await sql_executor.simulate_analyzed_updates(statements)
                    is_correct = (
                        user_answer_value in scene.get("branches", {})
                        and execution.get("affected_rows", 0) > 0
                    )
                    if not is_correct:
                        feedback = (
                            "Запрос не изменил выбор или указал недопустимое значение",
                        )
                else:
                    verification_query = expected_result.get("verification_query")
                    verification_result = expected_result.get("verification_result")
                    if not verification_query or not verification_result:
                        raise HTTPException(
                            status_code=500,
                            detail="Для UPDATE-сцены не настроена контрольная проверка",
                        )
                    execution = await sql_executor.simulate_analyzed_updates(
                        statements,
                        verification_query=str(verification_query),
                    )
                    comparison = sql_result_comparator.compare(
                        actual=QueryResult.from_mapping(execution),
                        expected=QueryResult.from_mapping(verification_result),
                        policy=QUEST_COMPARISON_POLICY,
                    )
                    is_correct = comparison.is_equal
                    if not is_correct:
                        feedback = tuple(
                            difference.message
                            for difference in comparison.differences
                        )
            else:
                feedback = tuple(
                    finding.message for finding in analysis.findings
                )

            if is_correct:
                quality_assessment = assess_query_quality(
                    analysis.findings,
                    100,
                    policy=quality_policy,
                )
                quality_penalty = quality_assessment.penalty_points
                feedback = quality_assessment.messages
            analysis_payload = build_analysis_payload(
                analysis,
                update_policy.task_context,
                penalty_policy=quality_policy,
                quality=quality_assessment,
            )
        else:
            if scene.get("expected_result"):
                submit_policy, quality_policy = configure_analysis(
                    SUBMIT_SELECT_POLICY,
                    question=scene.get("task") or "",
                    expected_result=scene["expected_result"],
                    tags=scene.get("tags"),
                )
                validation = await sql_validation_service.validate(
                    ValidationRequest(
                        sql=request.sql_query,
                        analysis_policy=submit_policy,
                        expected_result=QueryResult.from_mapping(
                            scene["expected_result"]
                        ),
                        comparison_policy=QUEST_COMPARISON_POLICY,
                    )
                )
                is_correct = validation.is_correct
                quality_assessment = None
                if is_correct:
                    quality_assessment = assess_query_quality(
                        validation.analysis.findings,
                        100,
                        policy=quality_policy,
                    )
                    quality_penalty = quality_assessment.penalty_points
                    feedback = quality_assessment.messages
                else:
                    feedback = validation.feedback
                analysis_payload = build_analysis_payload(
                    validation.analysis,
                    submit_policy.task_context,
                    penalty_policy=quality_policy,
                    quality=quality_assessment,
                )
            else:
                is_correct = True
    except Exception as error:
        is_correct = False
        feedback = (str(getattr(error, "detail", error)),)

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
            await scoring_service.add_points(
                current_user.user_id,
                100 - quality_penalty,
            )
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
            "earned": 100 - quality_penalty if is_correct else 0,
            "penalty": quality_penalty if is_correct else 10,
        },
        "is_quest_completed": is_quest_completed,
        "awarded_achievements": [],
        "feedback": list(feedback),
        "analysis": analysis_payload,
    }
