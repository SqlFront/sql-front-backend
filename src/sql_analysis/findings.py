"""

Структурированные результаты статического анализа.

"""
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from src.sql_analysis.facts import QueryFacts
from src.sql_analysis.parser import ParsedQuery


# Типы "серьезности" сообщения
class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Типы замечаний
class FindingCategory(StrEnum):
    SYNTAX = "syntax"
    SECURITY = "security"
    REQUIREMENT = "requirement"
    STYLE = "style"
    EFFICIENCY = "efficiency"  # Это не значит ошибка, а скорее недочет. Пока хз че с этим делать. Думаем


@dataclass(frozen=True)
class SourceLocation:
    """Позиция проблемного фрагмента в исходном SQL."""

    line: int
    column: int
    end_line: int
    end_column: int
    snippet: str


# Отдельная проблема, обнаруженная при анализе текста запроса
@dataclass(frozen=True)
class AnalysisFinding:
    """
        code: Стабильный машинный код для тестов, фронтенда и аналитики
        message: Понятное пользователю описание замечания
        severity: Уровень важности
        category: Тип замечания
        rule_id: ID правила, создавшего замечание
        blocks_execution: Запрещает ли замечание выполнение SQL в базе данных
        location: Позиция проблемного фрагмента в исходном SQL
        details: Дополнительные данные
    """

    code: str
    message: str
    severity: Severity
    category: FindingCategory
    rule_id: str
    blocks_execution: bool = False
    location: SourceLocation | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


# Итог статического анализа одного SQL-запроса
@dataclass(frozen=True)
class AnalysisResult:
    """
        parsed_query: Результат парсинга (или None при синтаксической ошибке)
        facts: Нормализованные сведения об AST (или None при ошибке парсинга)
        findings: Все замечания, собранные парсером и правилами
        has_errors: Есть ли среди замечаний хотя бы одна ошибка
        can_execute: Безопасно ли передавать запрос на выполнение в БД
    """

    parsed_query: ParsedQuery | None
    facts: QueryFacts | None
    findings: tuple[AnalysisFinding, ...]

    @property
    def has_errors(self) -> bool:
        return any(x.severity == Severity.ERROR for x in self.findings)

    @property
    def can_execute(self) -> bool:
        return not any(finding.blocks_execution for finding in self.findings)
