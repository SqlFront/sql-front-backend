"""Правило ограничения количества SQL-операторов."""

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule


class StatementCountRule(AnalysisRule):
    """Запрещает передавать больше операторов, чем разрешено политикой."""

    rule_id = "statement_count"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        actual_count = len(context.parsed_query.statements)
        allowed_count = context.policy.max_statement_count

        if actual_count <= allowed_count:
            return []

        return [AnalysisFinding(
            code="security.too_many_statements",
            message=(
                f"Разрешено SQL-операторов: {allowed_count}, "
                f"получено: {actual_count}"
            ),
            severity=Severity.ERROR,
            category=FindingCategory.SECURITY,
            rule_id=self.rule_id,
            blocks_execution=True,
            details={
                "allowed_count": allowed_count,
                "actual_count": actual_count,
            },
        )]
