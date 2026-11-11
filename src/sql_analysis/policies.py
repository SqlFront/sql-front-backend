"""Настройки статического анализа для разных режимов и типов заданий."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskAnalysisContext:
    """Контекст, необходимый для проверки решения конкретного задания."""

    question: str = ""
    difficulty: str = "unspecified"
    schema: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    strict_schema: bool = False

    def __post_init__(self) -> None:
        normalized_schema = {
            str(table).casefold(): tuple(
                str(column).casefold() for column in columns
            )
            for table, columns in (self.schema or {}).items()
        }
        object.__setattr__(self, "schema", normalized_schema)
        normalized_difficulty = self.difficulty.casefold()
        if normalized_difficulty not in {"easy", "medium", "hard", "unspecified"}:
            normalized_difficulty = "unspecified"
        object.__setattr__(self, "difficulty", normalized_difficulty)

    @classmethod
    def from_mapping(
            cls,
            value: Mapping[str, Any] | None,
            *,
            question: str = "",
            difficulty: str = "unspecified",
    ) -> "TaskAnalysisContext":
        payload = value or {}
        schema = payload.get("schema", {})
        if not isinstance(schema, Mapping):
            raise TypeError("schema должна быть объектом таблица -> список столбцов")
        for table, columns in schema.items():
            if isinstance(columns, (str, bytes)) or not isinstance(columns, Sequence):
                raise TypeError(f"Столбцы таблицы {table} должны быть списком")
        return cls(
            question=str(payload.get("question") or question),
            difficulty=str(payload.get("difficulty") or difficulty),
            schema={str(table): tuple(map(str, columns)) for table, columns in schema.items()},
            strict_schema=bool(payload.get("strict_schema", bool(schema))),
        )


@dataclass(frozen=True)
class QueryRequirements:
    """Декларативные требования конкретного учебного задания."""

    required_features: frozenset[str] = frozenset()
    forbidden_features: frozenset[str] = frozenset()
    required_tables: frozenset[str] = frozenset()
    required_functions: frozenset[str] = frozenset()
    required_selected_columns: frozenset[str] = frozenset()
    required_output_aliases: frozenset[str] = frozenset()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "QueryRequirements":
        """Создаёт требования из JSON-подобной конфигурации задания."""
        if value is None:
            return cls()

        field_names = (
            "required_features",
            "forbidden_features",
            "required_tables",
            "required_functions",
            "required_selected_columns",
            "required_output_aliases",
        )
        values: dict[str, frozenset[str]] = {}

        for field_name in field_names:
            raw_items = value.get(field_name, ())
            if isinstance(raw_items, (str, bytes)) or not isinstance(
                    raw_items,
                    Sequence,
            ):
                raise TypeError(f"{field_name} должен быть списком строк")
            if not all(isinstance(item, str) for item in raw_items):
                raise TypeError(f"{field_name} должен содержать только строки")
            values[field_name] = frozenset(
                item.casefold() for item in raw_items
            )

        return cls(**values)

    def with_tag_features(self, tags: Sequence[str] | None) -> "QueryRequirements":
        """Добавляет известные SQL-конструкции из тегов задания."""
        if not tags:
            return self

        tag_feature_map = {
            "join": "join",
            "group_by": "group_by",
            "order_by": "order_by",
            "limit": "limit",
            "distinct": "distinct",
            "cte": "cte",
            "subquery": "subquery",
            "window": "window_function",
            "aggregate": "aggregate_function",
            "union": "union",
            "intersect": "intersect",
            "except": "except",
        }
        tag_features = {
            feature
            for tag in tags
            if (feature := tag_feature_map.get(tag.casefold())) is not None
        }
        return QueryRequirements(
            required_features=self.required_features | tag_features,
            forbidden_features=self.forbidden_features,
            required_tables=self.required_tables,
            required_functions=self.required_functions,
            required_selected_columns=self.required_selected_columns,
            required_output_aliases=self.required_output_aliases,
        )


@dataclass(frozen=True)
class AnalysisPolicy:
    """
    allowed_statement_types: Разрешённые корневые типы SQL-операторов.
    forbidden_tables: Таблицы, обращение к которым запрещено.
    allowed_tables: Таблицы, разрешённые заданием; None снимает ограничение.
    max_statement_count: Максимальное количество SQL-операторов.
    allow_select_star: Разрешено ли использовать SELECT * и table.*.
    """

    allowed_statement_types: frozenset[str]
    forbidden_tables: frozenset[str] = frozenset()
    allowed_tables: frozenset[str] | None = None
    max_statement_count: int = 1
    allow_select_star: bool = False
    requirements: QueryRequirements = QueryRequirements()
    task_context: TaskAnalysisContext = TaskAnalysisContext()

    def __post_init__(self) -> None:
        if self.max_statement_count < 1:
            raise ValueError("max_statement_count должен быть не меньше 1")


SELECT_STATEMENT_TYPES = frozenset({
    "select",
    "union",
    "intersect",
    "except",
})

PROTECTED_TABLES = frozenset({
    "users",
    "password_hashes",
    "user_refresh_tokens",
    "user_events",
})

PREVIEW_SELECT_POLICY = AnalysisPolicy(
    allowed_statement_types=SELECT_STATEMENT_TYPES,
    forbidden_tables=PROTECTED_TABLES,
    allow_select_star=True,
)

SUBMIT_SELECT_POLICY = AnalysisPolicy(
    allowed_statement_types=SELECT_STATEMENT_TYPES,
    forbidden_tables=PROTECTED_TABLES,
    allow_select_star=False,
)

UPDATE_POLICY = AnalysisPolicy(
    allowed_statement_types=frozenset({"update"}),
    forbidden_tables=PROTECTED_TABLES,
)

# Обратная совместимость для кода, использующего прежнее имя политики.
DEFAULT_SELECT_POLICY = SUBMIT_SELECT_POLICY
