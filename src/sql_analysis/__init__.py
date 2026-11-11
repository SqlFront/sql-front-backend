"""Публичный интерфейс пакета статического анализа SQL."""

from src.sql_analysis.analyzer import SQLAnalyzer
from src.sql_analysis.ddl import (
    DEFAULT_DDL_POLICY,
    DDLAnalysisPolicy,
    DDLAnalysisResult,
    PostgresDDLAnalyzer,
)
from src.sql_analysis.findings import (
    AnalysisFinding,
    AnalysisResult,
    FindingCategory,
    Severity,
    SourceLocation,
)
from src.sql_analysis.policies import (
    DEFAULT_SELECT_POLICY,
    PREVIEW_SELECT_POLICY,
    SUBMIT_SELECT_POLICY,
    UPDATE_POLICY,
    AnalysisPolicy,
    QueryRequirements,
    TaskAnalysisContext,
)


__all__ = [
    "AnalysisFinding",
    "AnalysisPolicy",
    "AnalysisResult",
    "DEFAULT_DDL_POLICY",
    "DEFAULT_SELECT_POLICY",
    "DDLAnalysisPolicy",
    "DDLAnalysisResult",
    "FindingCategory",
    "PREVIEW_SELECT_POLICY",
    "PostgresDDLAnalyzer",
    "QueryRequirements",
    "SQLAnalyzer",
    "SUBMIT_SELECT_POLICY",
    "Severity",
    "SourceLocation",
    "TaskAnalysisContext",
    "UPDATE_POLICY",
]
