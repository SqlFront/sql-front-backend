"""Проверки гибридного анализатора PostgreSQL DDL и PL/pgSQL."""

from src.sql_analysis import PostgresDDLAnalyzer
from src.sql_validation import assess_query_quality


FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION get_enlistment_age(p_soldier_id INT)
RETURNS INT AS $$
DECLARE v_age INT;
BEGIN
    SELECT (EXTRACT(YEAR FROM enlistment_date) - birth_year)::INT
    INTO v_age FROM soldier WHERE id = p_soldier_id;
    RETURN v_age;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION log_equipment_addition()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO equipment_audit (item_name, added_at)
    VALUES (NEW.item_name, CURRENT_DATE);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_equipment_insert
AFTER INSERT ON equipment
FOR EACH ROW EXECUTE FUNCTION log_equipment_addition();
"""


def test_analyzer_accepts_function_with_plpgsql_body() -> None:
    result = PostgresDDLAnalyzer().analyze(FUNCTION_SQL)

    assert result.can_execute is True
    assert result.object_types == ("function",)
    assert len(result.statements) == 1


def test_analyzer_keeps_function_body_semicolons_inside_statement() -> None:
    result = PostgresDDLAnalyzer().analyze(TRIGGER_SQL)

    assert result.can_execute is True
    assert result.object_types == ("function", "trigger")
    assert len(result.statements) == 2


def test_analyzer_rejects_appended_statement() -> None:
    result = PostgresDDLAnalyzer().analyze(
        FUNCTION_SQL + " SELECT * FROM users;"
    )

    assert result.can_execute is False
    assert "security.ddl_statement_forbidden" in {
        finding.code for finding in result.findings
    }


def test_analyzer_rejects_dangerous_operation_in_body() -> None:
    sql = """
    CREATE FUNCTION dangerous() RETURNS VOID AS $$
    BEGIN
        EXECUTE 'DROP DATABASE game_db';
    END;
    $$ LANGUAGE plpgsql;
    """

    result = PostgresDDLAnalyzer().analyze(sql)

    assert result.can_execute is False
    assert "security.dangerous_ddl" in {
        finding.code for finding in result.findings
    }


def test_analyzer_rejects_unclosed_dollar_quote() -> None:
    result = PostgresDDLAnalyzer().analyze(
        "CREATE FUNCTION broken() RETURNS VOID AS $$ BEGIN RETURN;"
    )

    assert result.can_execute is False
    assert "syntax.invalid_ddl" in {
        finding.code for finding in result.findings
    }


def test_analyzer_reports_unused_parameter_and_constant_return() -> None:
    result = PostgresDDLAnalyzer().analyze("""
    CREATE OR REPLACE FUNCTION get_enlistment_age(p_soldier_id INT)
    RETURNS INT AS $$
    BEGIN
        RETURN 18;
    END;
    $$ LANGUAGE plpgsql;
    """)

    codes = {finding.code for finding in result.findings}
    assert result.can_execute is True
    assert "style.ddl_unused_parameter" in codes
    assert "efficiency.ddl_constant_return" in codes
    assert "efficiency.ddl_redundant_plpgsql" in codes
    assert all(not finding.blocks_execution for finding in result.findings)

    quality = assess_query_quality(result.findings, available_points=100)
    assert quality.penalty_points == 25
    assert set(finding.code for finding in quality.findings) == {
        "style.ddl_unused_parameter",
        "efficiency.ddl_constant_return",
        "efficiency.ddl_redundant_plpgsql",
    }


def test_analyzer_does_not_mark_used_parameter_as_unused() -> None:
    result = PostgresDDLAnalyzer().analyze(FUNCTION_SQL)

    assert "style.ddl_unused_parameter" not in {
        finding.code for finding in result.findings
    }


def test_analyzer_recommends_explicit_function_properties() -> None:
    result = PostgresDDLAnalyzer().analyze(FUNCTION_SQL)
    codes = {finding.code for finding in result.findings}

    assert "style.ddl_implicit_volatility" in codes
    assert "style.ddl_implicit_null_behavior" in codes

    explicit = PostgresDDLAnalyzer().analyze(
        FUNCTION_SQL.replace(
            "$$ LANGUAGE plpgsql;",
            "$$ LANGUAGE plpgsql STABLE CALLED ON NULL INPUT;",
        )
    )
    explicit_codes = {finding.code for finding in explicit.findings}
    assert "style.ddl_implicit_volatility" not in explicit_codes
    assert "style.ddl_implicit_null_behavior" not in explicit_codes
