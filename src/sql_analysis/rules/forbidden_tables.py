"""Правило запрета доступа к системным и служебным таблицам."""

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule
from src.sql_analysis.locations import locate_fragment


class ForbiddenTablesRule(AnalysisRule):
    """Находит физические таблицы, запрещённые политикой или системой."""

    rule_id = "forbidden_tables"
    system_schemas = frozenset({"information_schema", "pg_catalog"})

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        forbidden_tables = {
            table.casefold()
            for table in context.policy.forbidden_tables
        }
        allowed_tables = (
            {
                table.casefold()
                for table in context.policy.allowed_tables
            }
            if context.policy.allowed_tables is not None
            else None
        )
        findings: list[AnalysisFinding] = []

        for table in sorted(context.facts.physical_tables):
            normalized_table = table.casefold()
            table_parts = normalized_table.split(".")
            unqualified_name = table_parts[-1]
            schema_name = table_parts[-2] if len(table_parts) > 1 else None

            if (
                normalized_table in forbidden_tables
                or unqualified_name in forbidden_tables
                or schema_name in self.system_schemas
                or unqualified_name.startswith("pg_")
            ):
                findings.append(AnalysisFinding(
                    code="security.forbidden_table",
                    message=f"Доступ к таблице {table} запрещён",
                    severity=Severity.ERROR,
                    category=FindingCategory.SECURITY,
                    rule_id=self.rule_id,
                    blocks_execution=True,
                    location=locate_fragment(context.parsed_query.source, table),
                    details={"table": table},
                ))
                continue

            if (
                allowed_tables is not None
                and normalized_table not in allowed_tables
                and unqualified_name not in allowed_tables
            ):
                findings.append(AnalysisFinding(
                    code="security.table_not_allowed",
                    message=f"Таблица {table} не разрешена в этом задании",
                    severity=Severity.ERROR,
                    category=FindingCategory.SECURITY,
                    rule_id=self.rule_id,
                    blocks_execution=True,
                    location=locate_fragment(context.parsed_query.source, table),
                    details={"table": table},
                ))

        return findings
