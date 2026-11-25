"""Интеграционная проверка учебного SQL на отдельном PostgreSQL."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from src.sql_analysis import PostgresDDLAnalyzer, SQLAnalyzer, SUBMIT_SELECT_POLICY, UPDATE_POLICY
from src.sql_validation import (
    QueryResult,
    SQLValidationService,
    ValidationRequest,
    assess_query_quality,
    build_analysis_payload,
)
from src.utils.sql_executor import SQLExecutor


TEST_DSN = os.getenv("SQLFRONT_TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.postgres_integration,
    pytest.mark.skipif(not TEST_DSN, reason="Укажите SQLFRONT_TEST_DATABASE_URL"),
]


@asynccontextmanager
async def isolated_database():
    url = make_url(TEST_DSN)
    if url.drivername != "postgresql+asyncpg" or url.database != "sqlfront_test":
        pytest.fail("Требуется postgresql+asyncpg и отдельная база sqlfront_test")

    executor = SQLExecutor(TEST_DSN)
    schema = f"test_{uuid4().hex}"
    try:
        async with executor.transaction_engine.begin() as connection:
            await connection.execute(text(f"CREATE SCHEMA {schema}"))
            await connection.execute(text(
                f"CREATE TABLE {schema}.items (id integer PRIMARY KEY, quantity integer)"
            ))
            await connection.execute(text(f"INSERT INTO {schema}.items VALUES (1, 4), (2, 9)"))
        try:
            yield executor, schema
        finally:
            async with executor.transaction_engine.begin() as connection:
                await connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
    finally:
        await executor.engine.dispose()
        await executor.transaction_engine.dispose()


def test_postgres_cte_returns_expected_result_with_style_feedback():
    async def scenario():
        async with isolated_database() as (executor, schema):
            verdict = await SQLValidationService(SQLAnalyzer(), executor).validate(
                ValidationRequest(
                    sql=f"""
                        WITH filtered AS (
                            SELECT id, quantity FROM {schema}.items WHERE quantity > 4
                        ), projected AS (
                            SELECT filtered.id, filtered.quantity FROM filtered
                        )
                        SELECT projected.id, projected.quantity FROM projected ORDER BY 1
                    """,
                    analysis_policy=SUBMIT_SELECT_POLICY,
                    expected_result=QueryResult(("id", "quantity"), ((2, 9),), 1),
                )
            )

            assert verdict.is_correct, verdict.feedback
            quality = assess_query_quality(verdict.analysis.findings, 100)
            payload = build_analysis_payload(
                verdict.analysis, SUBMIT_SELECT_POLICY.task_context, quality=quality
            )
            assert quality.awarded_points == 95
            assert any(f["code"] == "style.order_by_ordinal" for f in payload["findings"])

    asyncio.run(scenario())


def test_postgres_update_checks_new_state_then_rolls_back():
    async def scenario():
        async with isolated_database() as (executor, schema):
            sql = f"UPDATE {schema}.items SET quantity = 12 WHERE id = 1"
            policy = replace(UPDATE_POLICY, allowed_tables=frozenset({f"{schema}.items"}))
            analysis = SQLAnalyzer().analyze(sql, policy)
            assert analysis.can_execute, analysis.findings

            check = f"SELECT quantity FROM {schema}.items WHERE id = 1"
            simulated = await executor.simulate_analyzed_updates([sql], check)
            assert simulated["data"] == [[12]]
            assert simulated["affected_rows"] == 1
            assert (await executor.execute_analyzed_sql(check))["data"] == [[4]]

    asyncio.run(scenario())


def test_postgres_plpgsql_function_runs_multiple_cases_then_rolls_back():
    async def scenario():
        async with isolated_database() as (executor, schema):
            sql = f"""
                CREATE FUNCTION {schema}.quantity_for(p_id integer)
                RETURNS integer LANGUAGE plpgsql STABLE AS $$
                BEGIN
                    RETURN (SELECT quantity FROM {schema}.items WHERE id = p_id);
                END;
                $$;
            """
            analysis = PostgresDDLAnalyzer().analyze(sql)
            assert analysis.can_execute, analysis.findings

            for item_id, expected in ((1, 4), (2, 9), (3, None)):
                result = await executor.simulate_analyzed_ddl(
                    sql, f"SELECT {schema}.quantity_for({item_id}) AS quantity"
                )
                assert result["data"] == [[expected]]

            gone = await executor.execute_analyzed_sql(
                f"SELECT to_regprocedure('{schema}.quantity_for(integer)') IS NULL AS gone"
            )
            assert gone["data"] == [[True]]

    asyncio.run(scenario())
