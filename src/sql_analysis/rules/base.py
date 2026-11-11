"""Базовые типы для правил статического анализа SQL."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from src.sql_analysis.facts import QueryFacts
from src.sql_analysis.findings import AnalysisFinding
from src.sql_analysis.parser import ParsedQuery
from src.sql_analysis.policies import AnalysisPolicy


@dataclass(frozen=True)
class AnalysisContext:
    """
    parsed_query: Разобранный SQL и его AST.
    facts: Нормализованные факты, извлечённые из AST.
    policy: Настройки, с которыми выполняется анализ.
    """

    parsed_query: ParsedQuery
    facts: QueryFacts
    policy: AnalysisPolicy


class AnalysisRule(ABC):
    """Общий контракт независимого правила анализа."""

    rule_id: ClassVar[str]

    def is_enabled(self, policy: AnalysisPolicy) -> bool:
        """Сообщает, должно ли правило запускаться для политики."""
        return True

    @abstractmethod
    def check(self, context: AnalysisContext) -> list[AnalysisFinding]:
        """Проверяет контекст и возвращает найденные замечания."""
        raise NotImplementedError
