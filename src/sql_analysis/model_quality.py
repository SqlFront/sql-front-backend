"""Рекомендации для SQL, который проверяет учебная модель каталога."""

from src.sql_analysis.findings import AnalysisFinding, FindingCategory, Severity
from src.utils.catalog_model import Cursor, ModelError, split_statements, tokenize


def analyze_model_quality(sql: str) -> tuple[AnalysisFinding, ...]:
    """Проверяет оформление операторов без изменения вердикта модели."""
    findings = []
    for number, statement in enumerate(split_statements(sql), start=1):
        cursor = Cursor(tokenize(statement))
        try:
            advice = _statement_advice(cursor)
        except ModelError:
            continue
        if advice is None:
            continue
        code, message = advice
        findings.append(AnalysisFinding(
            code=code,
            message=f"Оператор {number}. {message}",
            severity=Severity.WARNING,
            category=FindingCategory.STYLE,
            rule_id="model_quality",
            details={"statement_number": number},
        ))
    return tuple(findings)


def _statement_advice(cursor: Cursor) -> tuple[str, str] | None:
    if cursor.take("INSERT"):
        cursor.expect("INTO")
        table = cursor.name()
        if cursor.at("VALUES"):
            return (
                "style.model_implicit_insert_columns",
                f"Укажите список столбцов после имени таблицы {table}. "
                "Тогда соответствие значений столбцам будет видно из запроса.",
            )
    elif cursor.take("ALTER") and cursor.take("TABLE"):
        table = cursor.name()
        if cursor.take("ADD") and cursor.at("CHECK", "UNIQUE", "PRIMARY", "FOREIGN"):
            return (
                "style.model_unnamed_constraint",
                f"Дайте ограничению таблицы {table} осмысленное имя через "
                "ADD CONSTRAINT. По имени его проще найти или изменить.",
            )
    elif cursor.take("GRANT") and cursor.at("ALL"):
        return (
            "style.model_grant_all",
            "Проверьте, нужны ли получателю все права. Если условие требует "
            "только отдельные привилегии, перечислите их явно.",
        )
    return None
