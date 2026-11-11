"""Правило декларативных требований учебного задания."""

from collections.abc import Iterable

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
)
from src.sql_analysis.rules.base import AnalysisContext, AnalysisRule


class QueryRequirementsRule(AnalysisRule):
    """Сравнивает факты запроса с требованиями из политики."""

    rule_id = "query_requirements"

    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        requirements = context.policy.requirements
        facts = context.facts
        findings: list[AnalysisFinding] = []

        feature_names = {feature.casefold() for feature in facts.features}
        table_names = _qualified_and_short_names(facts.physical_tables)
        function_names = {name.casefold() for name in facts.function_names}
        column_names = _qualified_and_short_names(facts.selected_columns)
        output_aliases = {alias.casefold() for alias in facts.output_aliases}

        findings.extend(_missing_finding(
            code="requirement.missing_features",
            label="конструкции SQL",
            required=requirements.required_features,
            actual=feature_names,
            rule_id=self.rule_id,
        ))
        findings.extend(_forbidden_finding(
            code="requirement.forbidden_features",
            label="запрещённые конструкции SQL",
            forbidden=requirements.forbidden_features,
            actual=feature_names,
            rule_id=self.rule_id,
        ))
        findings.extend(_missing_finding(
            code="requirement.missing_tables",
            label="таблицы",
            required=requirements.required_tables,
            actual=table_names,
            rule_id=self.rule_id,
        ))
        findings.extend(_missing_finding(
            code="requirement.missing_functions",
            label="функции",
            required=requirements.required_functions,
            actual=function_names,
            rule_id=self.rule_id,
        ))
        findings.extend(_missing_finding(
            code="requirement.missing_columns",
            label="столбцы SELECT",
            required=requirements.required_selected_columns,
            actual=column_names,
            rule_id=self.rule_id,
        ))
        findings.extend(_missing_finding(
            code="requirement.missing_aliases",
            label="псевдонимы результата",
            required=requirements.required_output_aliases,
            actual=output_aliases,
            rule_id=self.rule_id,
        ))

        return findings


def _qualified_and_short_names(values: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for value in values:
        normalized = value.casefold()
        names.add(normalized)
        names.add(normalized.rsplit(".", maxsplit=1)[-1])
    return names


def _missing_finding(
        code: str,
        label: str,
        required: frozenset[str],
        actual: set[str],
        rule_id: str,
) -> list[AnalysisFinding]:
    missing = sorted(item.casefold() for item in required if item.casefold() not in actual)
    if not missing:
        return []

    return [AnalysisFinding(
        code=code,
        message=f"В запросе отсутствуют обязательные {label}: {', '.join(missing)}",
        severity=Severity.ERROR,
        category=FindingCategory.REQUIREMENT,
        rule_id=rule_id,
        blocks_execution=True,
        details={"missing": tuple(missing)},
    )]


def _forbidden_finding(
        code: str,
        label: str,
        forbidden: frozenset[str],
        actual: set[str],
        rule_id: str,
) -> list[AnalysisFinding]:
    found = sorted(item.casefold() for item in forbidden if item.casefold() in actual)
    if not found:
        return []

    return [AnalysisFinding(
        code=code,
        message=f"Запрос использует {label}: {', '.join(found)}",
        severity=Severity.ERROR,
        category=FindingCategory.REQUIREMENT,
        rule_id=rule_id,
        blocks_execution=True,
        details={"found": tuple(found)},
    )]
