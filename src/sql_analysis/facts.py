"""
Извлечение нормализованных фактов из AST.

"""
from dataclasses import dataclass

import sqlglot.expressions as exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from src.sql_analysis.parser import ParsedQuery


@dataclass(frozen=True)
class QuerySource:
    """Источник данных, видимый внутри одного SELECT."""

    alias: str
    name: str
    kind: str


@dataclass(frozen=True)
class QueryColumnReference:
    """Ссылка на столбец внутри области видимости."""

    sql: str
    name: str
    qualifier: str | None


@dataclass(frozen=True)
class QueryScopeFacts:
    """Факты одного SELECT с учётом вложенности и локальных псевдонимов."""

    scope_id: int
    parent_scope_id: int | None
    scope_type: str
    sources: tuple[QuerySource, ...]
    columns: tuple[QueryColumnReference, ...]
    duplicate_aliases: frozenset[str]

    @property
    def visible_source_count(self) -> int:
        return len(self.sources)


# Структурные свойства SQL-запроса, извлечённые из AST
@dataclass(frozen=True)
class QueryFacts:
    """
        statement_types: Тип каждого SQL-оператора
        physical_tables: Реальные таблицы, используемые запросом
        cte_names: Имена объявленных CTE
        selected_columns: Столбцы, указанные в SELECT
        output_aliases: Псевдонимы проекций во всех SELECT запроса
        function_names: Имена использованных SQL-функций
        order_by_columns: Выражения, используемые для сортировки
        features: Обнаруженные конструкции SQL
        has_select_star: Используется ли звёздочка в проекции SELECT
        scopes: Области видимости SELECT и их локальные источники
    """
    statement_types: tuple[str, ...]
    physical_tables: frozenset[str]
    cte_names: frozenset[str]
    selected_columns: tuple[str, ...]
    output_aliases: tuple[str, ...]
    function_names: frozenset[str]
    order_by_columns: tuple[str, ...]
    features: frozenset[str]
    has_select_star: bool
    scopes: tuple[QueryScopeFacts, ...]


# Вспомогательная функция для определения полного имени таблицы
def get_qualified_table_name(table: exp.Table) -> str:
    parts = (table.catalog, table.db, table.name,)
    return ".".join(part
                    for part in parts if part)


# Вспомогательная функция для проверки звездочек в SELECT
def is_select_star(expression: exp.Expression) -> bool:
    if isinstance(expression, exp.Star):
        return True

    if isinstance(expression, exp.Column):
        return isinstance(expression.this, exp.Star)

    return False


# Вспомогательная функция для определения имени функции
def get_function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return function.name.upper()

    return function.sql_name().upper()


# Вспомогательная функция для проверки наличия выражений определенного типа
def has_expression(
        parsed_query: ParsedQuery,
        expression_type: type[exp.Expression],
) -> bool:
    return any(
        statement.find(expression_type) is not None
        for statement in parsed_query.statements
    )


# Вспомогательная функция для поиска выражений
def extract_features(parsed_query: ParsedQuery) -> frozenset[str]:
    features: set[str] = set()

    feature_types = {
        "join": exp.Join,
        "group_by": exp.Group,
        "order_by": exp.Order,
        "limit": exp.Limit,
        "offset": exp.Offset,
        "cte": exp.CTE,
        "subquery": exp.Subquery,
        "window_function": exp.Window,
        "aggregate_function": exp.AggFunc,
        "union": exp.Union,
        "intersect": exp.Intersect,
        "except": exp.Except,
    }

    for feature_name, expression_type in feature_types.items():
        if has_expression(parsed_query, expression_type):
            features.add(feature_name)

    if any(
            select.args.get("distinct") is not None
            for statement in parsed_query.statements
            for select in statement.find_all(exp.Select)
    ):
        features.add("distinct")

    return frozenset(features)


# Вытаскиваем факты из запроса
def extract_query_facts(parsed_query: ParsedQuery) -> QueryFacts:
    statement_types = tuple(
        statement.key.lower()
        for statement in parsed_query.statements
    )

    cte_names = frozenset(
        cte.alias_or_name.casefold()
        for statement in parsed_query.statements
        for cte in statement.find_all(exp.CTE)
    )

    statement_scopes = [
        (statement, traverse_scope(statement))
        for statement in parsed_query.statements
    ]
    sqlglot_scopes = [
        scope
        for _, scopes_for_statement in statement_scopes
        for scope in scopes_for_statement
    ]
    scopes = _extract_scopes(sqlglot_scopes)
    physical_table_names = {
        source.name
        for scope in scopes
        for source in scope.sources
        if source.kind == "table"
    }
    for statement, scopes_for_statement in statement_scopes:
        if scopes_for_statement:
            continue
        physical_table_names.update(
            get_qualified_table_name(table).casefold()
            for table in statement.find_all(exp.Table)
        )
    physical_tables = frozenset(physical_table_names)

    has_select_star = any(
        is_select_star(projection)
        for statement in parsed_query.statements
        for select in statement.find_all(exp.Select)
        for projection in select.expressions
    )

    selected_columns = tuple(
        column.sql(dialect="postgres")
        for statement in parsed_query.statements
        for select in statement.find_all(exp.Select)
        for projection in select.expressions
        for column in projection.find_all(exp.Column)
        if (
                column.find_ancestor(exp.Select) is select
                and not isinstance(column.this, exp.Star)
        )
    )

    output_aliases = tuple(
        alias.alias
        for statement in parsed_query.statements
        for alias in statement.find_all(exp.Alias)
    )

    function_names = frozenset(
        get_function_name(function)
        for statement in parsed_query.statements
        for function in statement.find_all(exp.Func)
    )

    order_by_columns = tuple(
        ordered_expression.sql(dialect="postgres")
        for statement in parsed_query.statements
        for order in statement.find_all(exp.Order)
        for ordered_expression in order.expressions
    )

    features = extract_features(parsed_query)

    return QueryFacts(
        statement_types=statement_types,
        physical_tables=physical_tables,
        cte_names=cte_names,
        selected_columns=selected_columns,
        output_aliases=output_aliases,
        function_names=function_names,
        order_by_columns=order_by_columns,
        features=features,
        has_select_star=has_select_star,
        scopes=scopes,
    )


def _extract_scopes(scopes: list[Scope]) -> tuple[QueryScopeFacts, ...]:
    """Преобразует внутренние Scope SQLGlot в стабильную модель проекта."""
    scope_ids = {id(scope): index + 1 for index, scope in enumerate(scopes)}
    result: list[QueryScopeFacts] = []

    for scope in scopes:
        references = list(scope.references)
        aliases = [alias.casefold() for alias, _ in references]
        duplicate_aliases = frozenset(
            alias for alias in aliases if aliases.count(alias) > 1
        )
        sources: list[QuerySource] = []

        for alias, expression in references:
            normalized_alias = alias.casefold()
            resolved = scope.sources.get(alias)
            if isinstance(resolved, Scope):
                kind = "cte" if expression.name.casefold() in scope.cte_sources else "subquery"
                name = expression.name.casefold() or normalized_alias
            elif isinstance(expression, exp.Table):
                kind = "table"
                name = get_qualified_table_name(expression).casefold()
            else:
                kind = "derived"
                name = normalized_alias

            source = QuerySource(
                alias=normalized_alias,
                name=name,
                kind=kind,
            )
            if source not in sources:
                sources.append(source)

        columns = tuple(
            QueryColumnReference(
                sql=column.sql(dialect="postgres"),
                name=column.name.casefold(),
                qualifier=column.table.casefold() if column.table else None,
            )
            for column in scope.columns
            if not isinstance(column.this, exp.Star)
        )
        result.append(QueryScopeFacts(
            scope_id=scope_ids[id(scope)],
            parent_scope_id=(
                scope_ids.get(id(scope.parent)) if scope.parent is not None else None
            ),
            scope_type=str(scope.scope_type).rsplit(".", maxsplit=1)[-1].casefold(),
            sources=tuple(sources),
            columns=columns,
            duplicate_aliases=duplicate_aliases,
        ))

    return tuple(result)
