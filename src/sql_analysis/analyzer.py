"""Координатор полного статического анализа SQL-запроса."""

from collections.abc import Iterable

from src.sql_analysis.facts import extract_query_facts
from src.sql_analysis.findings import (
    AnalysisFinding,
    AnalysisResult,
    FindingCategory,
    Severity,
    SourceLocation,
)
from src.sql_analysis.parser import SQLParseError, SQLParser
from src.sql_analysis.policies import AnalysisPolicy
from src.sql_analysis.rules import DEFAULT_RULES, AnalysisContext, AnalysisRule


class SQLAnalyzer:
    """Запускает парсер, извлечение фактов и включённые правила анализа."""

    def __init__(
            self,
            parser: SQLParser | None = None,
            rules: Iterable[AnalysisRule] | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._rules = tuple(DEFAULT_RULES if rules is None else rules)

    def analyze(self, sql: str, policy: AnalysisPolicy) -> AnalysisResult:
        """Анализирует SQL, не выполняя его в базе данных."""
        try:
            parsed_query = self._parser.parse(sql)
        except SQLParseError as error:
            location = None
            if error.line is not None and error.column is not None:
                source_lines = sql.splitlines()
                snippet = (
                    source_lines[error.line - 1].strip()
                    if 0 < error.line <= len(source_lines) else ""
                )
                highlight_length = max(len(error.highlight or ""), 1)
                location = SourceLocation(
                    line=error.line,
                    column=error.column,
                    end_line=error.line,
                    end_column=error.column + highlight_length,
                    snippet=snippet,
                )
            return AnalysisResult(
                parsed_query=None,
                facts=None,
                findings=(AnalysisFinding(
                    code="syntax.invalid_sql",
                    message="Не удалось разобрать SQL-запрос",
                    severity=Severity.ERROR,
                    category=FindingCategory.SYNTAX,
                    rule_id="parser",
                    blocks_execution=True,
                    location=location,
                    details={"reason": str(error)},
                ),),
            )

        facts = extract_query_facts(parsed_query)
        context = AnalysisContext(
            parsed_query=parsed_query,
            facts=facts,
            policy=policy,
        )
        findings: list[AnalysisFinding] = []

        for rule in self._rules:
            if rule.is_enabled(policy):
                findings.extend(rule.check(context))

        return AnalysisResult(
            parsed_query=parsed_query,
            facts=facts,
            findings=tuple(findings),
        )
