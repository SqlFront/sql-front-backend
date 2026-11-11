"""Преобразование внутренних результатов анализа в стабильный API-контракт."""

from typing import Any

from src.sql_analysis.findings import AnalysisFinding, AnalysisResult
from src.sql_analysis.policies import TaskAnalysisContext
from src.sql_validation.quality import QualityAssessment, QualityPenaltyPolicy


def serialize_finding(
        finding: AnalysisFinding,
        penalty_policy: QualityPenaltyPolicy | None = None,
) -> dict[str, Any]:
    location = finding.location
    return {
        "code": finding.code,
        "message": finding.message,
        "severity": finding.severity.value,
        "category": finding.category.value,
        "rule_id": finding.rule_id,
        "blocks_execution": finding.blocks_execution,
        "penalty_rate": (
            penalty_policy.penalty_rates.get(finding.code, 0.0)
            if penalty_policy is not None else 0.0
        ),
        "location": (
            {
                "line": location.line,
                "column": location.column,
                "end_line": location.end_line,
                "end_column": location.end_column,
                "snippet": location.snippet,
            }
            if location is not None else None
        ),
        "details": dict(finding.details),
    }


def build_analysis_payload(
        analysis: AnalysisResult,
        task_context: TaskAnalysisContext,
        *,
        penalty_policy: QualityPenaltyPolicy | None = None,
        quality: QualityAssessment | None = None,
) -> dict[str, Any]:
    """Формирует данные для панели подсказок рядом с SQL-редактором."""
    return build_findings_payload(
        analysis.findings,
        task_context,
        penalty_policy=penalty_policy,
        quality=quality,
    )


def build_findings_payload(
        analysis_findings: tuple[AnalysisFinding, ...],
        task_context: TaskAnalysisContext,
        *,
        penalty_policy: QualityPenaltyPolicy | None = None,
        quality: QualityAssessment | None = None,
) -> dict[str, Any]:
    """Формирует API-ответ для AST и структурных DDL-анализаторов."""
    findings = [
        serialize_finding(finding, penalty_policy)
        for finding in analysis_findings
    ]
    payload: dict[str, Any] = {
        "context": {
            "question": task_context.question,
            "difficulty": task_context.difficulty,
            "schema": {
                table: list(columns)
                for table, columns in task_context.schema.items()
            },
        },
        "summary": {
            "issue_count": len(findings),
            "blocking_issue_count": sum(
                1 for finding in findings if finding["blocks_execution"]
            ),
            "warning_count": sum(
                1 for finding in findings if finding["severity"] == "warning"
            ),
        },
        "findings": findings,
        "grading": None,
    }
    if quality is not None:
        payload["grading"] = {
            "grade": quality.grade.value,
            "label": quality.grade_label,
            "score_percent": quality.score_percent,
            "available_points": quality.available_points,
            "points_after_quality": quality.awarded_points,
            "penalty_points": quality.penalty_points,
            "penalty_rate": quality.penalty_rate,
        }
    return payload


def build_analysis_error_detail(
        message: str,
        analysis_findings: tuple[AnalysisFinding, ...],
        task_context: TaskAnalysisContext,
        *,
        penalty_policy: QualityPenaltyPolicy | None = None,
) -> dict[str, Any]:
    """Формирует стабильное тело preview-ошибки со структурированными findings."""
    return {
        "message": message,
        "analysis": build_findings_payload(
            analysis_findings,
            task_context,
            penalty_policy=penalty_policy,
        ),
    }
