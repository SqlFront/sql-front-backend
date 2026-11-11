"""Гибкая оценка качества корректного SQL-решения."""

from dataclasses import dataclass, field
from enum import StrEnum
import math
from typing import Any, Mapping

from src.sql_analysis.findings import AnalysisFinding


BASE_PENALTY_RATES: Mapping[str, float] = {
    "style.implicit_join": 0.10,
    "style.unqualified_columns": 0.05,
    "style.order_by_ordinal": 0.05,
    "efficiency.redundant_distinct": 0.05,
    "style.ddl_unused_parameter": 0.10,
    "efficiency.ddl_constant_return": 0.10,
    "efficiency.ddl_redundant_plpgsql": 0.05,
}

DIFFICULTY_PENALTY_RATES: Mapping[str, Mapping[str, float]] = {
    "easy": BASE_PENALTY_RATES,
    "medium": {
        **BASE_PENALTY_RATES,
        "style.missing_table_alias": 0.05,
    },
    "hard": {
        **BASE_PENALTY_RATES,
        "style.missing_table_alias": 0.05,
        "style.complex_expression_without_alias": 0.05,
    },
}


class QualityGrade(StrEnum):
    """Учебная градация качества правильного решения."""

    SATISFACTORY = "satisfactory"
    GOOD = "good"
    EXCELLENT = "excellent"


GRADE_LABELS: Mapping[QualityGrade, str] = {
    QualityGrade.SATISFACTORY: "Удовлетворительно",
    QualityGrade.GOOD: "Хорошо",
    QualityGrade.EXCELLENT: "Отлично",
}


@dataclass(frozen=True)
class GradeThresholds:
    satisfactory: float = 0.0
    good: float = 0.75
    excellent: float = 0.90

    def __post_init__(self) -> None:
        if not (
            0 <= self.satisfactory <= self.good <= self.excellent <= 1
        ):
            raise ValueError("Пороги качества должны возрастать от 0 до 1")


@dataclass(frozen=True)
class QualityPenaltyPolicy:
    """Настраиваемые штрафы и пороги оценки для конкретного задания."""

    penalty_rates: Mapping[str, float] = field(
        default_factory=lambda: dict(DIFFICULTY_PENALTY_RATES["medium"])
    )
    max_penalty_rate: float = 0.30
    thresholds: GradeThresholds = GradeThresholds()

    def __post_init__(self) -> None:
        if not 0 <= self.max_penalty_rate <= 1:
            raise ValueError("max_penalty_rate должен находиться между 0 и 1")
        if any(not 0 <= rate <= 1 for rate in self.penalty_rates.values()):
            raise ValueError("Доли штрафов должны находиться между 0 и 1")

    @classmethod
    def from_mapping(
            cls,
            value: Mapping[str, Any] | None,
            *,
            difficulty: str = "medium",
    ) -> "QualityPenaltyPolicy":
        """Создаёт политику из конфигурации задания с безопасными defaults."""
        normalized_difficulty = difficulty.casefold()
        defaults = dict(DIFFICULTY_PENALTY_RATES.get(
            normalized_difficulty,
            DIFFICULTY_PENALTY_RATES["medium"],
        ))
        payload = value or {}
        overrides = payload.get("penalty_rates", {})
        if not isinstance(overrides, Mapping):
            raise TypeError("penalty_rates должен быть объектом код -> доля")
        defaults.update({str(code): float(rate) for code, rate in overrides.items()})

        raw_thresholds = payload.get("grade_thresholds", {})
        if not isinstance(raw_thresholds, Mapping):
            raise TypeError("grade_thresholds должен быть объектом")
        thresholds = GradeThresholds(
            satisfactory=float(raw_thresholds.get("satisfactory", 0.0)),
            good=float(raw_thresholds.get("good", 0.75)),
            excellent=float(raw_thresholds.get("excellent", 0.90)),
        )
        default_cap = {"easy": 0.25, "medium": 0.30, "hard": 0.35}.get(
            normalized_difficulty,
            0.30,
        )
        return cls(
            penalty_rates=defaults,
            max_penalty_rate=float(payload.get("max_penalty_rate", default_cap)),
            thresholds=thresholds,
        )


@dataclass(frozen=True)
class QualityAssessment:
    """Баллы, количество замечаний и итоговая градация решения."""

    available_points: int
    penalty_points: int
    penalty_rate: float
    awarded_points: int
    score_percent: int
    grade: QualityGrade
    findings: tuple[AnalysisFinding, ...]

    @property
    def messages(self) -> tuple[str, ...]:
        return tuple(finding.message for finding in self.findings)

    @property
    def issue_count(self) -> int:
        return len(self.findings)

    @property
    def grade_label(self) -> str:
        return GRADE_LABELS[self.grade]


def assess_query_quality(
        findings: tuple[AnalysisFinding, ...],
        available_points: int,
        policy: QualityPenaltyPolicy | None = None,
) -> QualityAssessment:
    """Переводит неблокирующие замечания в баллы и учебную оценку."""
    active_policy = policy or QualityPenaltyPolicy()
    penalized_findings = tuple(
        finding
        for finding in findings
        if not finding.blocks_execution
        and finding.code in active_policy.penalty_rates
    )
    unique_codes = {finding.code for finding in penalized_findings}
    penalty_rate = min(
        sum(active_policy.penalty_rates[code] for code in unique_codes),
        active_policy.max_penalty_rate,
    )
    penalty_points = (
        math.ceil(available_points * penalty_rate)
        if available_points > 0
        else 0
    )
    awarded_points = max(available_points - penalty_points, 0)
    ratio = awarded_points / available_points if available_points > 0 else 0.0

    if ratio >= active_policy.thresholds.excellent:
        grade = QualityGrade.EXCELLENT
    elif ratio >= active_policy.thresholds.good:
        grade = QualityGrade.GOOD
    else:
        grade = QualityGrade.SATISFACTORY

    return QualityAssessment(
        available_points=available_points,
        penalty_points=penalty_points,
        penalty_rate=penalty_rate,
        awarded_points=awarded_points,
        score_percent=round(ratio * 100),
        grade=grade,
        findings=penalized_findings,
    )
