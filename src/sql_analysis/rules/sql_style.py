"""Неблокирующие проверки качества и читаемости SQL."""

import sqlglot.expressions as exp

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.locations import locate_fragment
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule


class SQLStyleRule(AnalysisRule):
    """Находит рабочие, но менее читаемые или избыточные конструкции."""

    rule_id = "sql_style"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        implicit_join = next((
            join
            for statement in context.parsed_query.statements
            for join in statement.find_all(exp.Join)
            if join.args.get("on") is None
            and join.args.get("using") is None
            and join.args.get("kind") is None
            and join.args.get("method") is None
        ), None)
        if implicit_join is not None:
            findings.append(_style_finding(
                code="style.implicit_join",
                message=(
                    "Используйте явный JOIN ... ON вместо перечисления таблиц "
                    "через запятую"
                ),
                context=context,
                fragment=implicit_join.this.sql(dialect="postgres"),
            ))

        ambiguous_scope = next((
            scope for scope in context.facts.scopes
            if scope.visible_source_count > 1
            and any(column.qualifier is None for column in scope.columns)
        ), None)
        if ambiguous_scope is not None:
            column = next(
                column for column in ambiguous_scope.columns
                if column.qualifier is None
            )
            findings.append(_style_finding(
                code="style.unqualified_columns",
                message=(
                    "В запросе с несколькими таблицами указывайте таблицу "
                    "или псевдоним перед именем столбца"
                ),
                context=context,
                fragment=column.sql,
                details={"scope_id": ambiguous_scope.scope_id},
            ))

        ordinal_order = next((
            (order, ordered)
            for statement in context.parsed_query.statements
            for order in statement.find_all(exp.Order)
            for ordered in order.expressions
            if isinstance(ordered.this, exp.Literal)
            and not ordered.this.is_string
        ), None)
        if ordinal_order is not None:
            findings.append(_style_finding(
                code="style.order_by_ordinal",
                message=(
                    "В ORDER BY лучше указывать имя столбца или выражение, "
                    "а не его порядковый номер"
                ),
                context=context,
                fragment=ordinal_order[0].sql(dialect="postgres"),
            ))

        redundant_distinct = next((
            select
            for statement in context.parsed_query.statements
            for select in statement.find_all(exp.Select)
            if select.args.get("distinct") is not None
            and select.args.get("group") is not None
        ), None)
        if redundant_distinct is not None:
            findings.append(_style_finding(
                code="efficiency.redundant_distinct",
                message=(
                    "DISTINCT обычно избыточен при GROUP BY по тем же "
                    "возвращаемым значениям"
                ),
                category=FindingCategory.EFFICIENCY,
                context=context,
                fragment="DISTINCT",
            ))

        difficulty = context.policy.task_context.difficulty
        if difficulty in {"medium", "hard"}:
            unaliased_source = next((
                source
                for scope in context.facts.scopes
                if len([item for item in scope.sources if item.kind == "table"]) > 1
                for source in scope.sources
                if source.kind == "table"
                and source.alias == source.name.rsplit(".", maxsplit=1)[-1]
            ), None)
            if unaliased_source is not None:
                findings.append(_style_finding(
                    code="style.missing_table_alias",
                    message=(
                        "В запросе с несколькими таблицами используйте короткие "
                        "и понятные псевдонимы таблиц"
                    ),
                    context=context,
                    fragment=unaliased_source.name,
                ))

        if difficulty == "hard":
            complex_projection = next((
                projection
                for statement in context.parsed_query.statements
                for select in statement.find_all(exp.Select)
                for projection in select.expressions
                if not isinstance(projection, (exp.Alias, exp.Column, exp.Star))
            ), None)
            if complex_projection is not None:
                findings.append(_style_finding(
                    code="style.complex_expression_without_alias",
                    message=(
                        "Дайте вычисляемому столбцу понятный псевдоним через AS"
                    ),
                    context=context,
                    fragment=complex_projection.sql(dialect="postgres"),
                ))

        return findings


def _style_finding(
        code: str,
        message: str,
        category: FindingCategory = FindingCategory.STYLE,
        context: AnalysisContext | None = None,
        fragment: str | None = None,
        details: dict | None = None,
) -> AnalysisFinding:
    return AnalysisFinding(
        code=code,
        message=message,
        severity=Severity.WARNING,
        category=category,
        rule_id="sql_style",
        blocks_execution=False,
        location=(
            locate_fragment(context.parsed_query.source, fragment)
            if context is not None else None
        ),
        details=details or {},
    )
