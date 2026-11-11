"""Публичный интерфейс гибридной проверки SQL-решений."""

from src.sql_validation.models import (
    ComparisonPolicy,
    ComparisonResult,
    ExecutionResult,
    ExpectedResult,
    QueryResult,
    ResultDifference,
    ValidationRequest,
    ValidationResult,
    VerdictStatus,
)
from src.sql_validation.result_comparator import ResultComparator
from src.sql_validation.quality import (
    GradeThresholds,
    QualityGrade,
    QualityAssessment,
    QualityPenaltyPolicy,
    assess_query_quality,
)
from src.sql_validation.service import SQLValidationService
from src.sql_validation.presentation import (
    build_analysis_error_detail,
    build_analysis_payload,
    build_findings_payload,
    serialize_finding,
)
from src.sql_validation.task_config import configure_analysis, difficulty_from_tags


__all__ = [
    "ComparisonPolicy",
    "ComparisonResult",
    "ExecutionResult",
    "ExpectedResult",
    "GradeThresholds",
    "QueryResult",
    "QualityGrade",
    "QualityAssessment",
    "QualityPenaltyPolicy",
    "ResultComparator",
    "ResultDifference",
    "SQLValidationService",
    "ValidationRequest",
    "ValidationResult",
    "VerdictStatus",
    "assess_query_quality",
    "build_analysis_payload",
    "build_analysis_error_detail",
    "build_findings_payload",
    "configure_analysis",
    "difficulty_from_tags",
    "serialize_finding",
]
