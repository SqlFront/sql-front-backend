"""Оркестратор гибридной проверки пользовательского SQL-решения."""

from typing import Any, Mapping, Protocol

from src.sql_analysis.analyzer import SQLAnalyzer
from src.sql_validation.models import (
    ExecutionResult,
    QueryResult,
    ValidationRequest,
    ValidationResult,
    VerdictStatus,
)
from src.sql_validation.result_comparator import ResultComparator


class SQLExecutorProtocol(Protocol):
    """Минимальный интерфейс исполнителя, необходимый сервису."""

    async def execute_analyzed_sql(
            self,
            sql_query: str,
    ) -> Mapping[str, Any] | ExecutionResult:
        """Выполняет проверенный SQL и возвращает табличный результат."""
        ...


class SQLValidationService:
    """Последовательно анализирует, выполняет и сравнивает SQL."""

    def __init__(
            self,
            analyzer: SQLAnalyzer,
            executor: SQLExecutorProtocol,
            comparator: ResultComparator | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._executor = executor
        self._comparator = comparator or ResultComparator()

    async def validate(self, request: ValidationRequest) -> ValidationResult:
        """Выполняет полный цикл проверки одного решения."""
        analysis = self._analyzer.analyze(
            request.sql,
            request.analysis_policy,
        )

        if not analysis.can_execute:
            status = (
                VerdictStatus.INVALID_SQL
                if any(
                    finding.code == "syntax.invalid_sql"
                    for finding in analysis.findings
                )
                else VerdictStatus.REJECTED
            )
            return ValidationResult(
                status=status,
                analysis=analysis,
                execution=None,
                comparison=None,
                feedback=tuple(
                    finding.message for finding in analysis.findings
                ),
            )

        try:
            raw_execution = await self._executor.execute_analyzed_sql(request.sql)
            execution = (
                raw_execution
                if isinstance(raw_execution, QueryResult)
                else QueryResult.from_mapping(raw_execution)
            )
        except Exception as error:
            return ValidationResult(
                status=VerdictStatus.RUNTIME_ERROR,
                analysis=analysis,
                execution=None,
                comparison=None,
                feedback=(str(getattr(error, "detail", error)),),
            )

        comparison = self._comparator.compare(
            actual=execution,
            expected=request.expected_result,
            policy=request.comparison_policy,
        )
        status = (
            VerdictStatus.CORRECT
            if comparison.is_equal
            else VerdictStatus.INCORRECT
        )
        feedback = (
            tuple(
                finding.message
                for finding in analysis.findings
                if not finding.blocks_execution
            ) or ("Результат запроса совпадает с ожидаемым",)
            if comparison.is_equal
            else tuple(
                difference.message
                for difference in comparison.differences
            )
        )

        return ValidationResult(
            status=status,
            analysis=analysis,
            execution=execution,
            comparison=comparison,
            feedback=feedback,
        )
