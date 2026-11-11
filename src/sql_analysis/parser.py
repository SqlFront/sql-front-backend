"""

Преобразование исходного SQL-текста в AST библиотеки SQLGlot.

"""
from dataclasses import dataclass

import sqlglot
import sqlglot.expressions as exp


# Результат синтаксического разбора SQL
@dataclass(frozen=True)
class ParsedQuery:
    """
    source: Исходный текст запроса без изменений
    statements: Найденные в тексте операторы
    """
    source: str
    statements: tuple[exp.Expression, ...]


# Ошибка синтаксического разбора SQL
class SQLParseError(ValueError):
    """SQL-текст не удалось преобразовать в AST."""

    def __init__(
            self,
            message: str,
            *,
            line: int | None = None,
            column: int | None = None,
            highlight: str | None = None,
    ) -> None:
        super().__init__(message)
        self.line = line
        self.column = column
        self.highlight = highlight


# Преобразует SQL-текст PostgreSQL в AST SQLGlot
class SQLParser:
    def parse(self, sql: str) -> ParsedQuery:
        try:
            parsed_statements = sqlglot.parse(sql, read="postgres")
        except sqlglot.errors.ParseError as error:
            details = error.errors[0] if error.errors else {}
            raise SQLParseError(
                str(error),
                line=details.get("line"),
                column=details.get("col"),
                highlight=details.get("highlight"),
            ) from error

        statements = tuple(
            statement
            for statement in parsed_statements
            if statement is not None
        )

        if not statements:
            raise SQLParseError("Запрос не содержит SQL-операторов")

        return ParsedQuery(
            source=sql,
            statements=statements,
        )
