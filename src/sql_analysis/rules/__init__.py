"""Независимые правила статического анализа SQL."""

from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule
from src.sql_analysis.rules.forbidden_tables import ForbiddenTablesRule
from src.sql_analysis.rules.query_requirements import QueryRequirementsRule
from src.sql_analysis.rules.select_star import SelectStarRule
from src.sql_analysis.rules.scope import QueryScopeRule, TaskSchemaRule
from src.sql_analysis.rules.sql_style import SQLStyleRule
from src.sql_analysis.rules.statement_count import StatementCountRule
from src.sql_analysis.rules.statement_type import StatementTypeRule


DEFAULT_RULES: tuple[AnalysisRule, ...] = (
    StatementCountRule(),
    StatementTypeRule(),
    ForbiddenTablesRule(),
    QueryScopeRule(),
    TaskSchemaRule(),
    SelectStarRule(),
    QueryRequirementsRule(),
    SQLStyleRule(),
)


__all__ = [
    "AnalysisContext",
    "AnalysisRule",
    "DEFAULT_RULES",
    "ForbiddenTablesRule",
    "QueryRequirementsRule",
    "QueryScopeRule",
    "SelectStarRule",
    "SQLStyleRule",
    "StatementCountRule",
    "StatementTypeRule",
    "TaskSchemaRule",
]
