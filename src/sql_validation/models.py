"""Внутренние модели полного цикла проверки SQL-решения."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Sequence

from src.sql_analysis.findings import AnalysisResult
from src.sql_analysis.policies import AnalysisPolicy


class VerdictStatus(StrEnum):
    """Возможные итоговые состояния проверки решения."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    INVALID_SQL = "invalid_sql"
    REJECTED = "rejected"
    RUNTIME_ERROR = "runtime_error"


@dataclass(frozen=True)
class QueryResult:
    """
    columns: Названия столбцов результата.
    rows: Строки результата в порядке, возвращённом базой данных.
    row_count: Количество строк результата или затронутых строк.
    """

    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    row_count: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "QueryResult":
        """Преобразует словарь старого SQLExecutor в типизированную модель."""
        columns = tuple(str(column) for column in value.get("columns", ()))
        raw_rows = value.get("data", ())

        if isinstance(raw_rows, (str, bytes)) or not isinstance(
                raw_rows,
                Sequence,
        ):
            raise TypeError("Поле data результата должно содержать список строк")

        rows: list[tuple[Any, ...]] = []
        for row in raw_rows:
            if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
                raise TypeError("Каждая строка результата должна быть списком")
            rows.append(tuple(row))

        row_count = value.get("row_count", len(rows))
        if not isinstance(row_count, int):
            raise TypeError("Поле row_count результата должно быть целым числом")

        return cls(
            columns=columns,
            rows=tuple(rows),
            row_count=row_count,
        )


ExecutionResult = QueryResult
ExpectedResult = QueryResult


@dataclass(frozen=True)
class ComparisonPolicy:
    """
    compare_columns: Нужно ли сравнивать названия и порядок столбцов.
    row_order_matters: Важен ли порядок строк результата.
    float_tolerance: Допустимая абсолютная погрешность чисел.
    max_differences: Максимальное число отличий в результате сравнения.
    """

    compare_columns: bool = True
    row_order_matters: bool = False
    float_tolerance: float | None = None
    max_differences: int = 20

    def __post_init__(self) -> None:
        if self.float_tolerance is not None and self.float_tolerance < 0:
            raise ValueError("float_tolerance не может быть отрицательной")
        if self.max_differences < 1:
            raise ValueError("max_differences должен быть не меньше 1")


@dataclass(frozen=True)
class ResultDifference:
    """
    code: Машинный код типа отличия.
    message: Понятное пользователю описание.
    expected: Ожидаемое значение или строка.
    actual: Фактическое значение или строка.
    """

    code: str
    message: str
    expected: Any = None
    actual: Any = None


@dataclass(frozen=True)
class ComparisonResult:
    """
    is_equal: Совпадает ли фактический результат с ожидаемым.
    columns_equal: Совпали ли столбцы с учётом политики.
    rows_equal: Совпали ли строки с учётом политики.
    differences: Найденные отличия, ограниченные настройкой max_differences.
    """

    is_equal: bool
    columns_equal: bool
    rows_equal: bool
    differences: tuple[ResultDifference, ...]


@dataclass(frozen=True)
class ValidationRequest:
    """
    sql: SQL-решение пользователя.
    analysis_policy: Политика статического анализа.
    expected_result: Ожидаемый табличный результат.
    comparison_policy: Правила сравнения результатов.
    """

    sql: str
    analysis_policy: AnalysisPolicy
    expected_result: ExpectedResult
    comparison_policy: ComparisonPolicy = ComparisonPolicy()


@dataclass(frozen=True)
class ValidationResult:
    """
    status: Итоговый вердикт проверки.
    analysis: Результат статического анализа.
    execution: Результат выполнения или None, если SQL не выполнялся.
    comparison: Результат сравнения или None, если сравнения не было.
    feedback: Сообщения, которые можно показать пользователю.
    """

    status: VerdictStatus
    analysis: AnalysisResult
    execution: ExecutionResult | None
    comparison: ComparisonResult | None
    feedback: tuple[str, ...] = ()

    @property
    def is_correct(self) -> bool:
        return self.status == VerdictStatus.CORRECT
