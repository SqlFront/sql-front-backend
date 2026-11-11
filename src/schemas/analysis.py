"""Pydantic-контракт структурированных результатов анализа SQL."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FindingLocationResponse(BaseModel):
    line: int
    column: int
    end_line: int
    end_column: int
    snippet: str


class AnalysisFindingResponse(BaseModel):
    code: str
    message: str
    severity: Literal["error", "warning", "info"]
    category: Literal["syntax", "security", "requirement", "style", "efficiency"]
    rule_id: str
    blocks_execution: bool
    penalty_rate: float = 0.0
    location: FindingLocationResponse | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AnalysisSummaryResponse(BaseModel):
    issue_count: int
    blocking_issue_count: int
    warning_count: int


class AnalysisContextResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    difficulty: str
    database_schema: dict[str, list[str]] = Field(
        default_factory=dict,
        alias="schema",
    )


class QualityGradingResponse(BaseModel):
    grade: Literal["satisfactory", "good", "excellent"]
    label: str
    score_percent: int
    available_points: int
    points_after_quality: int
    penalty_points: int
    penalty_rate: float


class SQLAnalysisResponse(BaseModel):
    context: AnalysisContextResponse
    summary: AnalysisSummaryResponse
    findings: list[AnalysisFindingResponse] = Field(default_factory=list)
    grading: QualityGradingResponse | None = None
