"""Сравнение фактического результата SQL с ожидаемым."""

from numbers import Number
from typing import Any

from src.sql_validation.models import (
    ComparisonPolicy,
    ComparisonResult,
    ExecutionResult,
    ExpectedResult,
    ResultDifference,
)


class ResultComparator:
    """Сравнивает табличные результаты с учётом заданной политики."""

    def compare(
            self,
            actual: ExecutionResult,
            expected: ExpectedResult,
            policy: ComparisonPolicy,
    ) -> ComparisonResult:
        columns_equal = (
            actual.columns == expected.columns
            if policy.compare_columns
            else True
        )

        if policy.row_order_matters:
            rows_equal, row_differences = self._compare_ordered_rows(
                actual.rows,
                expected.rows,
                policy,
            )
        else:
            rows_equal, row_differences = self._compare_unordered_rows(
                actual.rows,
                expected.rows,
                policy,
            )

        differences: list[ResultDifference] = []
        if not columns_equal:
            differences.append(ResultDifference(
                code="columns_mismatch",
                message="Названия или порядок столбцов не совпадают",
                expected=expected.columns,
                actual=actual.columns,
            ))

        if actual.row_count != expected.row_count:
            rows_equal = False
            differences.append(ResultDifference(
                code="row_count_mismatch",
                message="Количество строк результата не совпадает",
                expected=expected.row_count,
                actual=actual.row_count,
            ))

        differences.extend(row_differences)

        return ComparisonResult(
            is_equal=columns_equal and rows_equal,
            columns_equal=columns_equal,
            rows_equal=rows_equal,
            differences=tuple(differences[:policy.max_differences]),
        )

    def _compare_ordered_rows(
            self,
            actual_rows: tuple[tuple[Any, ...], ...],
            expected_rows: tuple[tuple[Any, ...], ...],
            policy: ComparisonPolicy,
    ) -> tuple[bool, list[ResultDifference]]:
        differences: list[ResultDifference] = []
        max_length = max(len(actual_rows), len(expected_rows))

        for index in range(max_length):
            actual = actual_rows[index] if index < len(actual_rows) else None
            expected = expected_rows[index] if index < len(expected_rows) else None

            if actual is not None and expected is not None:
                rows_match = self._rows_equal(actual, expected, policy)
            else:
                rows_match = actual is expected

            if not rows_match and len(differences) < policy.max_differences:
                differences.append(ResultDifference(
                    code="row_mismatch",
                    message=f"Строка {index + 1} не совпадает",
                    expected=expected,
                    actual=actual,
                ))

        return not differences and len(actual_rows) == len(expected_rows), differences

    def _compare_unordered_rows(
            self,
            actual_rows: tuple[tuple[Any, ...], ...],
            expected_rows: tuple[tuple[Any, ...], ...],
            policy: ComparisonPolicy,
    ) -> tuple[bool, list[ResultDifference]]:
        unmatched_expected = list(expected_rows)
        unexpected_rows: list[tuple[Any, ...]] = []

        for actual_row in actual_rows:
            match_index = next(
                (
                    index
                    for index, expected_row in enumerate(unmatched_expected)
                    if self._rows_equal(actual_row, expected_row, policy)
                ),
                None,
            )
            if match_index is None:
                unexpected_rows.append(actual_row)
            else:
                unmatched_expected.pop(match_index)

        differences: list[ResultDifference] = []
        for row in unexpected_rows:
            if len(differences) >= policy.max_differences:
                break
            differences.append(ResultDifference(
                code="unexpected_row",
                message="Получена лишняя или отличающаяся строка",
                actual=row,
            ))

        for row in unmatched_expected:
            if len(differences) >= policy.max_differences:
                break
            differences.append(ResultDifference(
                code="missing_row",
                message="В результате отсутствует ожидаемая строка",
                expected=row,
            ))

        rows_equal = not unexpected_rows and not unmatched_expected
        return rows_equal, differences

    def _rows_equal(
            self,
            actual: tuple[Any, ...],
            expected: tuple[Any, ...],
            policy: ComparisonPolicy,
    ) -> bool:
        return (
            len(actual) == len(expected)
            and all(
                self._values_equal(actual_value, expected_value, policy)
                for actual_value, expected_value in zip(actual, expected)
            )
        )

    @staticmethod
    def _values_equal(
            actual: Any,
            expected: Any,
            policy: ComparisonPolicy,
    ) -> bool:
        if isinstance(actual, bool) or isinstance(expected, bool):
            return type(actual) is type(expected) and actual == expected

        if (
            policy.float_tolerance is not None
            and isinstance(actual, Number)
            and isinstance(expected, Number)
        ):
            return abs(float(actual) - float(expected)) <= policy.float_tolerance

        return actual == expected
