"""Правило использования звёздочки в проекции SELECT."""

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule
from src.sql_analysis.locations import locate_fragment


class SelectStarRule(AnalysisRule):
    """Требует перечислять возвращаемые столбцы явно."""

    rule_id = "select_star"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        if context.policy.allow_select_star:
            return []

        if not context.facts.has_select_star:
            return []

        return [AnalysisFinding(
            code="requirement.select_star_forbidden",
            message="Перечислите возвращаемые столбцы явно",
            severity=Severity.ERROR,
            category=FindingCategory.REQUIREMENT,
            rule_id=self.rule_id,
            blocks_execution=True,
            location=locate_fragment(context.parsed_query.source, "*"),
        )]
