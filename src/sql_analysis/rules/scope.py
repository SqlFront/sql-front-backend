"""Проверки областей видимости, псевдонимов и схемы задания."""

from src.sql_analysis.findings import AnalysisFinding, FindingCategory, Severity
from src.sql_analysis.locations import locate_fragment
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule


class QueryScopeRule(AnalysisRule):
    """Проверяет локальные псевдонимы в CTE и вложенных SELECT."""

    rule_id = "query_scope"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        scopes = {scope.scope_id: scope for scope in context.facts.scopes}

        for scope in context.facts.scopes:
            visible_aliases = _visible_aliases(scope.scope_id, scopes)

            for alias in sorted(scope.duplicate_aliases):
                findings.append(AnalysisFinding(
                    code="scope.duplicate_alias",
                    message=(
                        f"Псевдоним {alias} повторяется в одной области видимости"
                    ),
                    severity=Severity.ERROR,
                    category=FindingCategory.REQUIREMENT,
                    rule_id=self.rule_id,
                    blocks_execution=True,
                    location=locate_fragment(context.parsed_query.source, alias),
                    details={"alias": alias, "scope_id": scope.scope_id},
                ))

            for column in scope.columns:
                if column.qualifier is None or column.qualifier in visible_aliases:
                    continue
                findings.append(AnalysisFinding(
                    code="scope.unknown_qualifier",
                    message=(
                        f"Псевдоним {column.qualifier} недоступен в этой части запроса"
                    ),
                    severity=Severity.ERROR,
                    category=FindingCategory.REQUIREMENT,
                    rule_id=self.rule_id,
                    blocks_execution=True,
                    location=locate_fragment(
                        context.parsed_query.source,
                        column.sql,
                    ),
                    details={
                        "qualifier": column.qualifier,
                        "column": column.name,
                        "scope_id": scope.scope_id,
                    },
                ))

        return findings


class TaskSchemaRule(AnalysisRule):
    """Сверяет физические таблицы и квалифицированные столбцы со схемой задания."""

    rule_id = "task_schema"

    def is_enabled(self, policy) -> bool:
        return policy.task_context.strict_schema and bool(policy.task_context.schema)

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        schema = context.policy.task_context.schema
        findings: list[AnalysisFinding] = []
        scopes = {scope.scope_id: scope for scope in context.facts.scopes}

        for table in sorted(context.facts.physical_tables):
            if _schema_columns(schema, table) is not None:
                continue
            findings.append(AnalysisFinding(
                code="schema.unknown_table",
                message=f"Таблица {table} отсутствует в схеме этого задания",
                severity=Severity.ERROR,
                category=FindingCategory.REQUIREMENT,
                rule_id=self.rule_id,
                blocks_execution=True,
                location=locate_fragment(context.parsed_query.source, table),
                details={"table": table},
            ))

        for scope in context.facts.scopes:
            table_sources = _visible_table_sources(scope.scope_id, scopes)
            for column in scope.columns:
                if not column.qualifier:
                    continue
                table = table_sources.get(column.qualifier)
                if table is None:
                    continue
                columns = _schema_columns(schema, table)
                if columns is None or column.name in columns:
                    continue
                findings.append(AnalysisFinding(
                    code="schema.unknown_column",
                    message=(
                        f"Столбец {column.name} отсутствует в таблице {table}"
                    ),
                    severity=Severity.ERROR,
                    category=FindingCategory.REQUIREMENT,
                    rule_id=self.rule_id,
                    blocks_execution=True,
                    location=locate_fragment(
                        context.parsed_query.source,
                        column.sql,
                    ),
                    details={"table": table, "column": column.name},
                ))

        return findings


def _visible_aliases(scope_id, scopes) -> set[str]:
    aliases: set[str] = set()
    current = scopes.get(scope_id)
    while current is not None:
        aliases.update(source.alias for source in current.sources)
        current = scopes.get(current.parent_scope_id)
    return aliases


def _schema_columns(schema, table: str) -> frozenset[str] | None:
    normalized = table.casefold()
    raw_columns = schema.get(normalized)
    if raw_columns is None:
        raw_columns = schema.get(normalized.rsplit(".", maxsplit=1)[-1])
    return frozenset(raw_columns) if raw_columns is not None else None


def _visible_table_sources(scope_id, scopes) -> dict[str, str]:
    sources: dict[str, str] = {}
    current = scopes.get(scope_id)
    while current is not None:
        for source in current.sources:
            if source.kind == "table":
                sources.setdefault(source.alias, source.name)
        current = scopes.get(current.parent_scope_id)
    return sources
