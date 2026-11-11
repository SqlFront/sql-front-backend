"""Чтение настроек анализа и оценивания из конфигурации задания."""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from src.sql_analysis.policies import (
    AnalysisPolicy,
    QueryRequirements,
    TaskAnalysisContext,
)
from src.sql_validation.quality import QualityPenaltyPolicy
from src.sql_validation.schema_catalog import schema_for_tables


def difficulty_from_tags(tags: Sequence[str] | None) -> str:
    normalized = {str(tag).casefold() for tag in (tags or ())}
    for difficulty in ("hard", "medium", "easy"):
        if difficulty in normalized:
            return difficulty
    return "medium"


def configure_analysis(
        base_policy: AnalysisPolicy,
        *,
        question: str,
        expected_result: Mapping[str, Any] | None,
        tags: Sequence[str] | None,
) -> tuple[AnalysisPolicy, QualityPenaltyPolicy]:
    """Объединяет вопрос, схему, требования, сложность и штрафы задания."""
    payload = expected_result or {}
    difficulty = difficulty_from_tags(tags)
    raw_context = payload.get("analysis_context")
    if raw_context is None and payload.get("analysis_schema") is not None:
        raw_context = {
            "schema": payload.get("analysis_schema"),
            "strict_schema": True,
        }
    if raw_context is not None and not isinstance(raw_context, Mapping):
        raise TypeError("analysis_context должен быть объектом")

    analysis_tables = payload.get("analysis_tables")
    if analysis_tables is not None:
        if isinstance(analysis_tables, (str, bytes)) or not isinstance(
                analysis_tables,
                Sequence,
        ):
            raise TypeError("analysis_tables должен быть списком строк")
        if not all(isinstance(table, str) for table in analysis_tables):
            raise TypeError("analysis_tables должен содержать только строки")

        raw_context = dict(raw_context or {})
        configured_schema = raw_context.get("schema")
        if configured_schema:
            raise ValueError(
                "Нельзя одновременно задавать analysis_tables и analysis_context.schema"
            )
        raw_context["schema"] = schema_for_tables(analysis_tables)
        raw_context.setdefault("strict_schema", True)

    task_context = TaskAnalysisContext.from_mapping(
        raw_context,
        question=question,
        difficulty=difficulty,
    )
    requirements = QueryRequirements.from_mapping(
        payload.get("analysis_requirements")
    )
    if payload.get("derive_requirements_from_tags", True):
        requirements = requirements.with_tag_features(tags)
    quality_policy = QualityPenaltyPolicy.from_mapping(
        payload.get("quality_policy"),
        difficulty=task_context.difficulty,
    )
    return (
        replace(
            base_policy,
            requirements=requirements,
            task_context=task_context,
        ),
        quality_policy,
    )
