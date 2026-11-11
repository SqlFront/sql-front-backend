"""Проверки базового конвейера статического анализа SQL."""

import pytest

from src.sql_analysis import (
    AnalysisPolicy,
    QueryRequirements,
    SQLAnalyzer,
    TaskAnalysisContext,
)


@pytest.fixture
def analyzer() -> SQLAnalyzer:
    return SQLAnalyzer()


@pytest.fixture
def select_policy() -> AnalysisPolicy:
    return AnalysisPolicy(
        allowed_statement_types=frozenset({"select", "union"}),
    )


def test_valid_select_can_be_executed(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze("SELECT id FROM users", select_policy)

    assert result.findings == ()
    assert result.has_errors is False
    assert result.can_execute is True


def test_select_star_is_blocked(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze("SELECT * FROM users", select_policy)

    assert [finding.code for finding in result.findings] == [
        "requirement.select_star_forbidden",
    ]
    assert result.can_execute is False


def test_count_star_is_not_select_star(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze("SELECT COUNT(*) FROM users", select_policy)

    assert result.findings == ()
    assert result.can_execute is True


def test_multiple_statements_are_blocked(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze(
        "SELECT id FROM users; SELECT id FROM orders",
        select_policy,
    )

    assert "security.too_many_statements" in {
        finding.code for finding in result.findings
    }
    assert result.can_execute is False


def test_forbidden_statement_type_is_blocked(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze("DELETE FROM users", select_policy)

    assert [finding.code for finding in result.findings] == [
        "security.statement_type_forbidden",
    ]
    assert result.can_execute is False


def test_forbidden_physical_table_is_blocked(analyzer: SQLAnalyzer) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
        forbidden_tables=frozenset({"users"}),
        allow_select_star=True,
    )

    result = analyzer.analyze(
        "WITH users AS (SELECT id FROM private_users) SELECT * FROM users",
        policy,
    )

    assert result.findings == ()

    result = analyzer.analyze("SELECT * FROM public.users", policy)

    assert [finding.code for finding in result.findings] == [
        "security.forbidden_table",
    ]
    assert result.can_execute is False


def test_invalid_sql_returns_analysis_result(
        analyzer: SQLAnalyzer,
        select_policy: AnalysisPolicy,
) -> None:
    result = analyzer.analyze("SELECT (", select_policy)

    assert result.parsed_query is None
    assert result.facts is None
    assert [finding.code for finding in result.findings] == [
        "syntax.invalid_sql",
    ]
    assert result.has_errors is True
    assert result.can_execute is False
    assert result.findings[0].location is not None
    assert result.findings[0].location.line == 1


def test_table_outside_allowlist_is_blocked(analyzer: SQLAnalyzer) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
        allowed_tables=frozenset({"users"}),
    )

    result = analyzer.analyze("SELECT id FROM orders", policy)

    assert [finding.code for finding in result.findings] == [
        "security.table_not_allowed",
    ]
    assert result.can_execute is False


def test_policy_can_allow_select_star(analyzer: SQLAnalyzer) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
        allow_select_star=True,
    )

    result = analyzer.analyze("SELECT * FROM users", policy)

    assert result.findings == ()
    assert result.can_execute is True


def test_policy_rejects_invalid_statement_limit() -> None:
    with pytest.raises(ValueError, match="не меньше 1"):
        AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
            max_statement_count=0,
        )


def test_query_requirements_accept_matching_facts(analyzer: SQLAnalyzer) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
        requirements=QueryRequirements(
            required_features=frozenset({
                "join",
                "group_by",
                "aggregate_function",
            }),
            required_tables=frozenset({"users", "orders"}),
            required_functions=frozenset({"count"}),
            required_selected_columns=frozenset({"id"}),
            required_output_aliases=frozenset({"order_count"}),
        ),
    )

    result = analyzer.analyze(
        """
        SELECT u.id, COUNT(o.id) AS order_count
        FROM users AS u
        JOIN orders AS o ON o.user_id = u.id
        GROUP BY u.id
        """,
        policy,
    )

    assert result.findings == ()
    assert result.can_execute is True


def test_query_requirements_report_missing_and_forbidden_facts(
        analyzer: SQLAnalyzer,
) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
        requirements=QueryRequirements.from_mapping({
            "required_features": ["group_by"],
            "forbidden_features": ["order_by"],
            "required_tables": ["orders"],
            "required_functions": ["count"],
            "required_selected_columns": ["total"],
            "required_output_aliases": ["order_count"],
        }),
    )

    result = analyzer.analyze(
        "SELECT id FROM users ORDER BY id",
        policy,
    )

    assert {finding.code for finding in result.findings} == {
        "requirement.missing_features",
        "requirement.forbidden_features",
        "requirement.missing_tables",
        "requirement.missing_functions",
        "requirement.missing_columns",
        "requirement.missing_aliases",
    }
    assert result.can_execute is False


def test_style_findings_do_not_block_correct_query(
        analyzer: SQLAnalyzer,
) -> None:
    policy = AnalysisPolicy(
        allowed_statement_types=frozenset({"select"}),
    )

    result = analyzer.analyze(
        "SELECT id FROM users, orders WHERE users.id = orders.user_id ORDER BY 1",
        policy,
    )

    assert {finding.code for finding in result.findings} == {
        "style.implicit_join",
        "style.unqualified_columns",
        "style.order_by_ordinal",
    }
    assert result.has_errors is False
    assert result.can_execute is True


def test_tags_add_only_known_query_features() -> None:
    requirements = QueryRequirements().with_tag_features([
        "join",
        "order_by",
        "easy",
        "supply",
    ])

    assert requirements.required_features == frozenset({
        "join",
        "order_by",
    })


def test_nested_cte_scope_keeps_real_tables_and_ignores_cte_reference(
        analyzer: SQLAnalyzer,
) -> None:
    result = analyzer.analyze(
        "WITH users AS (SELECT id FROM private_users) SELECT * FROM users",
        AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
            allow_select_star=True,
        ),
    )

    assert result.facts is not None
    assert result.facts.physical_tables == frozenset({"private_users"})


def test_correlated_subquery_can_reference_outer_alias(
        analyzer: SQLAnalyzer,
) -> None:
    result = analyzer.analyze(
        """
        SELECT u.id
        FROM users AS u
        WHERE EXISTS (
            SELECT 1 FROM orders AS o WHERE o.user_id = u.id
        )
        """,
        AnalysisPolicy(allowed_statement_types=frozenset({"select"})),
    )

    assert "scope.unknown_qualifier" not in {
        finding.code for finding in result.findings
    }
    assert result.can_execute is True


def test_duplicate_alias_is_reported_in_its_scope(
        analyzer: SQLAnalyzer,
) -> None:
    result = analyzer.analyze(
        "SELECT x.id FROM users AS x JOIN orders AS x ON x.id = x.user_id",
        AnalysisPolicy(allowed_statement_types=frozenset({"select"})),
    )

    finding = next(
        finding for finding in result.findings
        if finding.code == "scope.duplicate_alias"
    )
    assert finding.blocks_execution is True
    assert finding.location is not None
    assert finding.location.line == 1


def test_task_schema_rejects_unknown_qualified_column(
        analyzer: SQLAnalyzer,
) -> None:
    result = analyzer.analyze(
        "SELECT s.unknown_column FROM soldier AS s",
        AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
            task_context=TaskAnalysisContext(
                question="Выведите имя солдата",
                difficulty="easy",
                schema={"soldier": ("id", "full_name")},
                strict_schema=True,
            ),
        ),
    )

    assert [finding.code for finding in result.findings] == [
        "schema.unknown_column",
    ]
    assert result.can_execute is False


def test_hard_task_enables_additional_quality_rules(
        analyzer: SQLAnalyzer,
) -> None:
    result = analyzer.analyze(
        "SELECT COUNT(u.id) FROM users u JOIN orders o ON o.user_id = u.id",
        AnalysisPolicy(
            allowed_statement_types=frozenset({"select"}),
            task_context=TaskAnalysisContext(difficulty="hard"),
        ),
    )

    assert "style.complex_expression_without_alias" in {
        finding.code for finding in result.findings
    }
