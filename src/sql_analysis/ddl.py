"""Гибридная структурная проверка PostgreSQL DDL и PL/pgSQL."""

from dataclasses import dataclass
import re

from sqlglot.errors import TokenError
from sqlglot.tokens import TokenType

from src.sql_analysis.findings import (
    AnalysisFinding,
    FindingCategory,
    Severity,
    SourceLocation,
)
from src.sql_analysis.plpgsql import (
    body_tokens,
    empty_control_blocks,
    referenced_names,
    token_spelling,
    unused_declarations,
)


@dataclass(frozen=True)
class DDLAnalysisPolicy:
    """Ограничения для учебных DDL-заданий."""

    allowed_object_types: frozenset[str] = frozenset({
        "function",
        "procedure",
        "trigger",
    })
    max_statement_count: int = 2


@dataclass(frozen=True)
class DDLAnalysisResult:
    """Результат структурной проверки DDL без построения SQLGlot AST."""

    statements: tuple[str, ...]
    object_types: tuple[str, ...]
    findings: tuple[AnalysisFinding, ...]

    @property
    def can_execute(self) -> bool:
        return not any(finding.blocks_execution for finding in self.findings)


DEFAULT_DDL_POLICY = DDLAnalysisPolicy()


class PostgresDDLAnalyzer:
    """Проверяет разрешённую оболочку DDL с dollar-quoted PL/pgSQL телом."""

    _create_pattern = re.compile(
        r"^CREATE\s+(?:(?:OR\s+REPLACE)\s+)?"
        r"(FUNCTION|PROCEDURE|TRIGGER)\b",
        re.IGNORECASE,
    )
    _forbidden_patterns = (
        re.compile(r"\b(?:DROP|TRUNCATE|GRANT|REVOKE)\b", re.IGNORECASE),
        re.compile(
            r"\bCREATE\s+(?:DATABASE|SCHEMA|ROLE|USER|EXTENSION)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bALTER\s+(?:SYSTEM|DATABASE|ROLE|USER)\b", re.IGNORECASE),
        re.compile(r"\bCOPY\b[^;]*\bPROGRAM\b", re.IGNORECASE | re.DOTALL),
        re.compile(r"\b(?:PG_READ_FILE|PG_READ_BINARY_FILE|PG_LS_DIR)\s*\(", re.IGNORECASE),
        re.compile(r"\b(?:DBLINK|LO_EXPORT)\s*\(", re.IGNORECASE),
    )

    def analyze(
            self,
            sql: str,
            policy: DDLAnalysisPolicy = DEFAULT_DDL_POLICY,
    ) -> DDLAnalysisResult:
        statements, syntax_error = _split_top_level_statements(sql)
        findings: list[AnalysisFinding] = []
        object_types: list[str] = []

        if syntax_error:
            findings.append(_finding(
                code="syntax.invalid_ddl",
                message=syntax_error,
                category=FindingCategory.SYNTAX,
            ))

        if not statements:
            findings.append(_finding(
                code="syntax.empty_ddl",
                message="DDL-запрос не содержит операторов",
                category=FindingCategory.SYNTAX,
            ))

        if len(statements) > policy.max_statement_count:
            findings.append(_finding(
                code="security.too_many_ddl_statements",
                message=(
                    f"Разрешено DDL-операторов: {policy.max_statement_count}, "
                    f"получено: {len(statements)}"
                ),
            ))

        for statement in statements:
            match = self._create_pattern.match(_strip_leading_comments(statement))
            if match is None:
                findings.append(_finding(
                    code="security.ddl_statement_forbidden",
                    message=(
                        "Разрешены только CREATE FUNCTION, PROCEDURE и TRIGGER"
                    ),
                ))
                continue

            object_type = match.group(1).casefold()
            object_types.append(object_type)
            if object_type not in policy.allowed_object_types:
                findings.append(_finding(
                    code="security.ddl_object_type_forbidden",
                    message=f"Создание объекта {object_type.upper()} запрещено",
                ))

        for pattern in self._forbidden_patterns:
            if pattern.search(sql):
                findings.append(_finding(
                    code="security.dangerous_ddl",
                    message="DDL содержит потенциально опасную операцию",
                ))
                break

        for statement in statements:
            findings.extend(_analyze_routine_quality(sql, statement))

        return DDLAnalysisResult(
            statements=statements,
            object_types=tuple(object_types),
            findings=tuple(findings),
        )


def _finding(
        code: str,
        message: str,
        category: FindingCategory = FindingCategory.SECURITY,
) -> AnalysisFinding:
    return AnalysisFinding(
        code=code,
        message=message,
        severity=Severity.ERROR,
        category=category,
        rule_id="ddl_structure",
        blocks_execution=True,
    )


def _quality_finding(
        *,
        code: str,
        message: str,
        category: FindingCategory,
        sql: str,
        start: int | None = None,
        end: int | None = None,
        details: dict[str, str] | None = None,
        severity: Severity = Severity.WARNING,
) -> AnalysisFinding:
    return AnalysisFinding(
        code=code,
        message=message,
        severity=severity,
        category=category,
        rule_id="ddl_quality",
        blocks_execution=False,
        location=(
            _source_location(sql, start, end)
            if start is not None else None
        ),
        details=details or {},
    )


def _source_location(sql: str, start: int, end: int | None = None) -> SourceLocation:
    bounded_start = max(0, min(start, len(sql)))
    bounded_end = max(bounded_start + 1, min(end or bounded_start + 1, len(sql)))
    line = sql.count("\n", 0, bounded_start) + 1
    line_start = sql.rfind("\n", 0, bounded_start) + 1
    column = bounded_start - line_start + 1
    end_line = sql.count("\n", 0, bounded_end) + 1
    end_line_start = sql.rfind("\n", 0, bounded_end) + 1
    end_column = bounded_end - end_line_start + 1
    snippet_end = sql.find("\n", line_start)
    if snippet_end == -1:
        snippet_end = len(sql)
    return SourceLocation(
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        snippet=sql[line_start:snippet_end].strip(),
    )


_routine_pattern = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?P<object_type>FUNCTION|PROCEDURE)\s+"
    r"(?P<name>(?:[\w\"]+\.)?[\w\"]+)\s*"
    r"\((?P<parameters>.*?)\)\s*"
    r"(?P<header>.*?)\bAS\s+"
    r"(?P<tag>\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$)"
    r"(?P<body>.*?)"
    r"(?P=tag)(?P<options>.*)$",
    re.IGNORECASE | re.DOTALL,
)


def _analyze_routine_quality(sql: str, statement: str) -> list[AnalysisFinding]:
    """Возвращает неблокирующие рекомендации для FUNCTION и PROCEDURE."""
    match = _routine_pattern.search(statement)
    if match is None:
        return []

    findings: list[AnalysisFinding] = []
    body = match.group("body")
    parameters = _input_parameter_names(match.group("parameters"))
    statement_offset = sql.find(statement)
    body_offset = statement_offset + match.start("body") if statement_offset >= 0 else 0
    options = f"{match.group('header')} {match.group('options')}"
    is_plpgsql = bool(re.search(
        r"\bLANGUAGE\s+(?:'plpgsql'|plpgsql)\b", options, re.IGNORECASE
    ))

    tokens = None
    if is_plpgsql:
        try:
            tokens = body_tokens(body)
        except TokenError:
            # Не делаем выводов о качестве по частично разобранному телу.
            pass

    names = referenced_names(tokens) if tokens is not None else set()
    positional_parameter = tokens is not None and any(
        token.token_type == TokenType.PARAMETER for token in tokens
    )
    for parameter in parameters:
        if is_plpgsql:
            if tokens is None or positional_parameter or parameter.casefold() in names:
                continue
        elif re.search(rf"\b{re.escape(parameter)}\b", body, re.IGNORECASE):
            continue
        parameter_match = re.search(
            rf"\b{re.escape(parameter)}\b",
            statement,
            re.IGNORECASE,
        )
        start = (
            statement_offset + parameter_match.start()
            if statement_offset >= 0 and parameter_match is not None else None
        )
        findings.append(_quality_finding(
            code="style.ddl_unused_parameter",
            message=(
                f"Параметр {parameter} не используется в теле функции. "
                "Используйте его в вычислении или удалите из сигнатуры."
            ),
            category=FindingCategory.STYLE,
            sql=sql,
            start=start,
            end=(start + len(parameter)) if start is not None else None,
            details={"parameter": parameter},
        ))

    words = [
        token_spelling(body, token).upper() for token in (tokens or ())
    ]
    return_end = words.index(";") if ";" in words else 0
    simple_return = (
        words[:2] == ["BEGIN", "RETURN"]
        and return_end > 2
        and words[return_end + 1:] in (["END"], ["END", ";"])
    )
    if simple_return:
        value_start = tokens[2].start
        value_end = tokens[return_end - 1].end + 1
        value = body[value_start:value_end]
    else:
        value = ""
    if re.fullmatch(
        r"[-+]?\d+(?:\.\d+)?|TRUE|FALSE|NULL|'(?:''|[^'])*'",
        value, re.IGNORECASE,
    ):
        findings.append(_quality_finding(
            code="efficiency.ddl_constant_return",
            message=(
                "Функция возвращает константу и не вычисляет результат по входным "
                "данным. Проверьте, соответствует ли это условию задания."
            ),
            category=FindingCategory.EFFICIENCY,
            sql=sql,
            start=body_offset + value_start,
            end=body_offset + value_end,
            details={"value": value},
        ))

    if simple_return and value and words[2] != "NEXT":
        findings.append(_quality_finding(
            code="efficiency.ddl_redundant_plpgsql",
            message=(
                "Тело состоит из одного RETURN. Для простой функции рассмотрите "
                "LANGUAGE SQL без избыточного блока BEGIN/END."
            ),
            category=FindingCategory.EFFICIENCY,
            sql=sql,
            start=body_offset,
            end=body_offset + len(body),
        ))

    if tokens is not None:
        for token in unused_declarations(body, tokens):
            findings.append(_quality_finding(
                code="style.plpgsql_unused_variable",
                message=f"Переменная {token.text} объявлена, но не используется. "
                        "Уберите объявление, если оно не нужно для решения.",
                category=FindingCategory.STYLE,
                sql=sql,
                start=body_offset + token.start,
                end=body_offset + token.end + 1,
                details={"variable": token.text},
            ))
        for kind, token in empty_control_blocks(body, tokens):
            message = (
                "Тело цикла пустое. Проверьте, какое действие должно повторяться."
                if kind == "loop" else
                "Ветка IF пустая. Проверьте, какое действие должно выполняться в ней."
            )
            findings.append(_quality_finding(
                code=f"style.plpgsql_empty_{kind}",
                message=message,
                category=FindingCategory.STYLE,
                sql=sql,
                start=body_offset + token.start,
                end=body_offset + token.end + 1,
            ))

    if match.group("object_type").casefold() == "function":
        routine_properties = options
        if not re.search(r"\b(?:IMMUTABLE|STABLE|VOLATILE)\b", routine_properties, re.IGNORECASE):
            findings.append(_quality_finding(
                code="style.ddl_implicit_volatility",
                message=(
                    "Свойство изменчивости функции не указано явно. Если функция "
                    "только читает таблицы, рассмотрите STABLE; для чистых вычислений — IMMUTABLE."
                ),
                category=FindingCategory.STYLE,
                sql=sql,
                severity=Severity.INFO,
            ))
        if parameters and not re.search(
                r"\b(?:STRICT|RETURNS\s+NULL\s+ON\s+NULL\s+INPUT|CALLED\s+ON\s+NULL\s+INPUT)\b",
                routine_properties,
                re.IGNORECASE,
        ):
            findings.append(_quality_finding(
                code="style.ddl_implicit_null_behavior",
                message=(
                    "Поведение функции при NULL-параметрах не указано явно. "
                    "При необходимости добавьте STRICT или CALLED ON NULL INPUT."
                ),
                category=FindingCategory.STYLE,
                sql=sql,
                severity=Severity.INFO,
            ))

    return findings


def _input_parameter_names(parameters: str) -> tuple[str, ...]:
    names: list[str] = []
    for raw_parameter in _split_parameters(parameters):
        tokens = raw_parameter.strip().split()
        if not tokens:
            continue
        mode = tokens[0].casefold()
        if mode == "out":
            continue
        if mode in {"in", "inout", "variadic"}:
            tokens = tokens[1:]
        if len(tokens) < 2:
            continue
        name = tokens[0].strip('"')
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", name):
            names.append(name)
    return tuple(names)


def _split_parameters(parameters: str) -> tuple[str, ...]:
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    in_quote = False
    for character in parameters:
        if character == "'":
            in_quote = not in_quote
        elif not in_quote and character == "(":
            depth += 1
        elif not in_quote and character == ")":
            depth = max(depth - 1, 0)
        elif not in_quote and character == "," and depth == 0:
            parts.append("".join(buffer))
            buffer.clear()
            continue
        buffer.append(character)
    if buffer:
        parts.append("".join(buffer))
    return tuple(parts)


def _strip_leading_comments(statement: str) -> str:
    value = statement.lstrip()
    while True:
        if value.startswith("--"):
            _, separator, value = value.partition("\n")
            if not separator:
                return ""
            value = value.lstrip()
            continue
        if value.startswith("/*"):
            end = value.find("*/", 2)
            if end == -1:
                return value
            value = value[end + 2:].lstrip()
            continue
        return value


def _split_top_level_statements(sql: str) -> tuple[tuple[str, ...], str | None]:
    """Делит SQL по `;`, игнорируя строки, комментарии и dollar quotes."""
    statements: list[str] = []
    buffer: list[str] = []
    index = 0
    state = "normal"
    dollar_tag = ""

    while index < len(sql):
        pair = sql[index:index + 2]
        character = sql[index]

        if state == "normal":
            dollar_match = re.match(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$", sql[index:])
            if dollar_match:
                dollar_tag = dollar_match.group(0)
                buffer.append(dollar_tag)
                index += len(dollar_tag)
                state = "dollar"
                continue
            if pair == "--":
                state = "line_comment"
                buffer.append(pair)
                index += 2
                continue
            if pair == "/*":
                state = "block_comment"
                buffer.append(pair)
                index += 2
                continue
            if character == "'":
                state = "single_quote"
            elif character == '"':
                state = "double_quote"
            elif character == ";":
                statement = "".join(buffer).strip()
                if statement:
                    statements.append(statement)
                buffer.clear()
                index += 1
                continue

        elif state == "dollar":
            if sql.startswith(dollar_tag, index):
                buffer.append(dollar_tag)
                index += len(dollar_tag)
                state = "normal"
                continue
        elif state == "line_comment":
            if character == "\n":
                state = "normal"
        elif state == "block_comment":
            if pair == "*/":
                buffer.append(pair)
                index += 2
                state = "normal"
                continue
        elif state in {"single_quote", "double_quote"}:
            quote = "'" if state == "single_quote" else '"'
            if character == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    buffer.append(quote)
                    index += 2
                    continue
                state = "normal"

        buffer.append(character)
        index += 1

    trailing = "".join(buffer).strip()
    if trailing:
        statements.append(trailing)

    if state != "normal" and state != "line_comment":
        return tuple(statements), "DDL содержит незакрытую строку или комментарий"
    return tuple(statements), None
