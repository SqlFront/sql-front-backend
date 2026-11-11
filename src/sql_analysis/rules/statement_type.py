"""Правило допустимых типов SQL-операторов."""

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule


class StatementTypeRule(AnalysisRule):
    """Запрещает корневые типы операторов, не разрешённые политикой."""

    rule_id = "statement_type"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        allowed_types = {
            statement_type.casefold()
            for statement_type in context.policy.allowed_statement_types
        }
        findings: list[AnalysisFinding] = []

        for statement_index, statement_type in enumerate(
                context.facts.statement_types,
                start=1,
        ):
            if statement_type.casefold() in allowed_types:
                continue

            findings.append(AnalysisFinding(
                code="security.statement_type_forbidden",
                message=(
                    f"SQL-оператор типа {statement_type.upper()} запрещён"
                ),
                severity=Severity.ERROR,
                category=FindingCategory.SECURITY,
                rule_id=self.rule_id,
                blocks_execution=True,
                details={
                    "statement_index": statement_index,
                    "statement_type": statement_type,
                    "allowed_statement_types": tuple(sorted(allowed_types)),
                },
            ))

        return findings
