import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
from fastapi import HTTPException

from config import settings
from src.api.task import submit_sql_query
from src.schemas.task import SQLRequest
from src.utils.sql_executor import SQLExecutor


def get_test_game_db_url() -> str:
    """Return a working database URL for game_db testing."""
    override = os.getenv("TEST_GAME_DB_URL")
    if override:
        return override

    candidates = [
        "postgresql+asyncpg://sql_runner:secret@localhost:5430/game_db",
        "postgresql+asyncpg://sql_runner:secret@localhost:5432/game_db",
        settings.GAME_DATABASE_URL,
    ]
    for url in candidates:
        dsn = url.replace("postgresql+asyncpg://", "postgresql://")
        try:
            async def _check():
                conn = await asyncio.wait_for(asyncpg.connect(dsn), timeout=1.5)
                await conn.close()

            asyncio.run(_check())
            return url
        except Exception:
            continue
    return "postgresql+asyncpg://sql_runner:secret@localhost:5430/game_db"


class TestMission5PLpgSQLExecutor(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_url = get_test_game_db_url()
        dsn = cls.db_url.replace("postgresql+asyncpg://", "postgresql://")
        try:
            async def _check():
                conn = await asyncio.wait_for(asyncpg.connect(dsn), timeout=2.0)
                await conn.close()

            asyncio.run(_check())
            cls.db_available = True
        except Exception:
            cls.db_available = False

    def setUp(self):
        if not self.db_available:
            self.skipTest(f"Database not available at {self.db_url}")
        self.executor = SQLExecutor(self.db_url)

    async def test_5_3_military_service_id_sequence_and_procedure(self):
        """Task 5.3: Procedure transfer_soldier inserts into military_service without id,

        verifying military_service.id default sequence prevents NOT NULL violation.
        """
        ddl = """
        CREATE OR REPLACE PROCEDURE transfer_soldier(p_soldier_id INT, p_new_unit_id INT) AS $$
        BEGIN
            UPDATE military_service SET end_date = CURRENT_DATE WHERE soldier_id = p_soldier_id AND end_date IS NULL;
            INSERT INTO military_service (soldier_id, unit_id, start_date) VALUES (p_soldier_id, p_new_unit_id, CURRENT_DATE);
        END;
        $$ LANGUAGE plpgsql;
        """
        test_query = (
            "CALL transfer_soldier(1, 2); "
            "SELECT unit_id FROM military_service WHERE soldier_id = 1 ORDER BY id DESC LIMIT 1;"
        )
        res = await self.executor.simulate_ddl(ddl, test_query, expect_error=False)
        self.assertEqual(res["columns"], ["unit_id"])
        self.assertEqual(res["data"], [[2]])
        self.assertEqual(res["row_count"], 1)

    async def test_5_4_multiple_statements_ddl(self):
        """Task 5.4: Multi-statement DDL (FUNCTION + TRIGGER) does not crash with

        'cannot insert multiple commands into a prepared statement'.
        """
        ddl = """
        CREATE OR REPLACE FUNCTION log_equipment_addition() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO equipment_audit (item_name, added_at) VALUES (NEW.item_name, CURRENT_DATE);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_after_equipment_insert AFTER INSERT ON equipment
        FOR EACH ROW EXECUTE FUNCTION log_equipment_addition();
        """
        test_query = (
            "INSERT INTO equipment (id, unit_id, equipment_type, item_name, quantity, last_replenishment) "
            "VALUES (9999, 1, 'тест', 'Тестовый образец', 1, CURRENT_DATE); "
            "SELECT item_name FROM equipment_audit WHERE item_name = 'Тестовый образец';"
        )
        res = await self.executor.simulate_ddl(ddl, test_query, expect_error=False)
        self.assertEqual(res["columns"], ["item_name"])
        self.assertEqual(res["data"], [["Тестовый образец"]])
        self.assertEqual(res["row_count"], 1)

    async def test_5_5_select_division_by_zero_fails_phase1(self):
        """Task 5.5: SELECT 1/0; or non-DDL runtime error must fail Phase 1 and NOT pass expect_error."""
        test_query = (
            "INSERT INTO soldier (id, full_name, birth_year, rank, branch, enlistment_city, enlistment_date) "
            "VALUES (9999, 'Малолетний боец', 1930, 'рядовой', 'пехота', 'Москва', '1941-01-01');"
        )
        with self.assertRaises(HTTPException) as ctx:
            await self.executor.simulate_ddl("SELECT 1/0;", test_query, expect_error=True)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Ошибка выполнения DDL", ctx.exception.detail)
        self.assertIn("division by zero", ctx.exception.detail)

    async def test_5_5_invalid_syntax_ddl_fails_phase1(self):
        """Task 5.5: Syntactically broken DDL must fail Phase 1."""
        test_query = (
            "INSERT INTO soldier (id, full_name, birth_year, rank, branch, enlistment_city, enlistment_date) "
            "VALUES (9999, 'Малолетний боец', 1930, 'рядовой', 'пехота', 'Москва', '1941-01-01');"
        )
        with self.assertRaises(HTTPException) as ctx:
            await self.executor.simulate_ddl(
                "CREATE OR REPLACE FUNCTION broken_syntax(", test_query, expect_error=True
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Ошибка выполнения DDL", ctx.exception.detail)

    async def test_5_5_non_blocking_trigger_fails_phase2(self):
        """Task 5.5: A trigger that does NOT raise an exception must fail Phase 2."""
        ddl = """
        CREATE OR REPLACE FUNCTION dummy_pass_soldier() RETURNS TRIGGER AS $$
        BEGIN
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_dummy_pass BEFORE INSERT ON soldier
        FOR EACH ROW EXECUTE FUNCTION dummy_pass_soldier();
        """
        test_query = (
            "INSERT INTO soldier (id, full_name, birth_year, rank, branch, enlistment_city, enlistment_date) "
            "VALUES (9999, 'Малолетний боец', 1930, 'рядовой', 'пехота', 'Москва', '1941-01-01');"
        )
        with self.assertRaises(HTTPException) as ctx:
            await self.executor.simulate_ddl(ddl, test_query, expect_error=True)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Ожидалась ошибка валидации", ctx.exception.detail)

    async def test_5_5_valid_trigger_blocks_invalid_insert(self):
        """Task 5.5: Valid trigger correctly raises exception and is caught with error_caught=True."""
        ddl = """
        CREATE OR REPLACE FUNCTION validate_soldier_age() RETURNS TRIGGER AS $$
        BEGIN
            IF (EXTRACT(YEAR FROM NEW.enlistment_date) - NEW.birth_year) < 16 THEN
                RAISE EXCEPTION 'Возраст призывника не может быть меньше 16 лет';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_before_soldier_insert BEFORE INSERT ON soldier
        FOR EACH ROW EXECUTE FUNCTION validate_soldier_age();
        """
        test_query = (
            "INSERT INTO soldier (id, full_name, birth_year, rank, branch, enlistment_city, enlistment_date) "
            "VALUES (9999, 'Малолетний боец', 1930, 'рядовой', 'пехота', 'Москва', '1941-01-01');"
        )
        res = await self.executor.simulate_ddl(ddl, test_query, expect_error=True)
        self.assertTrue(res.get("error_caught"))
        self.assertIn("Возраст призывника не может быть меньше 16 лет", res["data"][0][0])


class TestSubmitSQLQueryMission5Validation(unittest.IsolatedAsyncioTestCase):
    """Unit tests for submit_sql_query endpoint verifying Task 5.5 marking behavior."""

    @patch("src.api.task.sql_executor")
    @patch("src.api.task.TaskRepository")
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    async def test_task_5_5_select_1_0_is_rejected(
        self, mock_log_event, mock_repo_class, mock_sql_executor
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_repo.get_task_info = AsyncMock(
            return_value=SimpleNamespace(
                task_global_id=110,
                expected_result={
                    "mode": "ddl",
                    "test_query": "INSERT INTO soldier ...",
                    "expect_error": True,
                },
            )
        )
        mock_sql_executor.simulate_ddl = AsyncMock(
            side_effect=HTTPException(
                status_code=400,
                detail="Ошибка выполнения DDL: division by zero",
            )
        )
        mock_repo.check_and_reward_task = AsyncMock(
            return_value={
                "was_solved_before": False,
                "points_earned": 0,
                "points_penalty": 10,
                "message": "Ответ неверный! Списано 10 баллов",
                "awarded_achievements": [],
                "current_points": 90,
            }
        )

        user = SimpleNamespace(user_id=1, total_score=100)
        db = AsyncMock()

        res = await submit_sql_query(
            mission_id=5,
            task_id=5,
            request=SQLRequest(sql_query="SELECT 1/0;"),
            current_user=user,
            db=db,
        )

        self.assertFalse(res["is_correct"])
        self.assertIn("Ошибка выполнения DDL", res["hint"])
        mock_repo.check_and_reward_task.assert_awaited_once_with(
            user_id=1,
            mission_id=5,
            task_id=5,
            is_correct=False,
        )

    @patch("src.api.task.sql_executor")
    @patch("src.api.task.TaskRepository")
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    async def test_task_5_5_valid_trigger_is_accepted(
        self, mock_log_event, mock_repo_class, mock_sql_executor
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_repo.get_task_info = AsyncMock(
            return_value=SimpleNamespace(
                task_global_id=110,
                expected_result={
                    "mode": "ddl",
                    "test_query": "INSERT INTO soldier ...",
                    "expect_error": True,
                },
            )
        )
        mock_sql_executor.simulate_ddl = AsyncMock(
            return_value={
                "columns": ["Результат"],
                "data": [["Исключение успешно перехвачено: Возраст призывника не может быть меньше 16 лет"]],
                "row_count": 1,
                "error_caught": True,
            }
        )
        mock_repo.check_and_reward_task = AsyncMock(
            return_value={
                "was_solved_before": False,
                "points_earned": 50,
                "points_penalty": 0,
                "message": "Правильно! Начислено 50 баллов",
                "awarded_achievements": [],
                "current_points": 150,
            }
        )
        mock_repo.add_solved_task = AsyncMock()

        user = SimpleNamespace(user_id=1, total_score=100)
        db = AsyncMock()

        valid_query = "CREATE OR REPLACE FUNCTION ...; CREATE TRIGGER ...;"
        res = await submit_sql_query(
            mission_id=5,
            task_id=5,
            request=SQLRequest(sql_query=valid_query),
            current_user=user,
            db=db,
        )

        self.assertTrue(res["is_correct"])
        self.assertEqual(res["hint"], "Триггер успешно заблокировал некорректную операцию")
        mock_repo.check_and_reward_task.assert_awaited_once_with(
            user_id=1,
            mission_id=5,
            task_id=5,
            is_correct=True,
            user_query=valid_query,
        )


if __name__ == "__main__":
    unittest.main()
