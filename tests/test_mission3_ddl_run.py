import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.api.task import run_sql_query
from src.schemas.task import SQLRequest
from src.utils.sql_executor import SQLExecutor


class TestExtractOperationType(unittest.TestCase):
    def test_extract_ddl_operations(self):
        cases = [
            ("CREATE TABLE podpolye.depots (id int)", "CREATE TABLE"),
            ("create view podpolye.v as select 1", "CREATE VIEW"),
            ("alter table podpolye.depots add column c int", "ALTER TABLE"),
            ("ALTER DATABASE quest_sandbox SET timezone TO 'UTC'", "ALTER DATABASE"),
            ("create schema podpolye", "CREATE SCHEMA"),
            ("create unique index idx_depot on t(id)", "CREATE INDEX"),
            ("grant select on podpolye.depots to scout", "GRANT"),
            ("revoke select on podpolye.depots from scout", "REVOKE"),
            ("comment on table t is 'desc'", "COMMENT"),
            ("CREATE OR REPLACE FUNCTION f() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql", "CREATE OR REPLACE FUNCTION"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(SQLExecutor._extract_operation_type(query), expected)


class TestSQLExecutorDDLSecurity(unittest.TestCase):
    def setUp(self):
        self.executor = SQLExecutor.__new__(SQLExecutor)

    def test_ddl_allowed_create_table(self):
        query = "CREATE TABLE podpolye.depots (depot_id int);"
        # Should not raise exception
        self.executor._validate_sql(query, allow_ddl=True)

    def test_ddl_allowed_alter_table(self):
        query = "ALTER TABLE podpolye.depots ADD COLUMN notes text;"
        # Should not raise exception
        self.executor._validate_sql(query, allow_ddl=True)

    def test_ddl_disallowed_by_default(self):
        query = "CREATE TABLE podpolye.depots (depot_id int);"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=False)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_forbidden_drop_database(self):
        query = "DROP DATABASE quest_sandbox;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=True)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_forbidden_alter_system(self):
        query = "ALTER SYSTEM SET max_connections = 100;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=True)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_forbidden_user_table_in_ddl(self):
        query = "CREATE TABLE leak AS SELECT * FROM users;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=True)
        self.assertEqual(ctx.exception.status_code, 400)


class TestMission3RunEndpoint(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = SimpleNamespace(user_id=1, total_score=100)
        self.mock_db = AsyncMock()

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_create_schema_success(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=84,
            mission_id=3,
            task_id=1,
            title="Создание схемы",
            tags=["ddl", "schema"],
            expected_result={
                "mode": "model",
                "database": "quest_sandbox",
                "setup": [],
                "expect": [{"probe": "schema_exists", "args": {"name": "podpolye"}, "value": True}],
            },
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(sql_query="CREATE SCHEMA podpolye")
        result = await run_sql_query(
            mission_id=3,
            task_id=1,
            request=req,
            current_user=self.user,
            db=self.mock_db,
        )

        self.assertEqual(result["columns"], ["Статус операции"])
        self.assertEqual(
            result["data"],
            [["Команда успешно выполнена: CREATE SCHEMA (симуляция завершена успешно)"]],
        )
        self.assertEqual(result["row_count"], 1)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_create_table_success(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=86,
            mission_id=3,
            task_id=3,
            title="Склады подполья",
            tags=["ddl", "table"],
            expected_result={
                "mode": "model",
                "database": "quest_sandbox",
                "setup": ["CREATE SCHEMA podpolye"],
                "expect": [],
            },
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(
            sql_query="CREATE TABLE podpolye.depots (depot_id integer PRIMARY KEY, depot_name varchar(50) NOT NULL);"
        )
        result = await run_sql_query(
            mission_id=3,
            task_id=3,
            request=req,
            current_user=self.user,
            db=self.mock_db,
        )

        self.assertEqual(result["columns"], ["Статус операции"])
        self.assertEqual(
            result["data"],
            [["Команда успешно выполнена: CREATE TABLE (симуляция завершена успешно)"]],
        )
        self.assertEqual(result["row_count"], 1)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_multiline_alter_database_success(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=85,
            mission_id=3,
            task_id=2,
            title="Настройка базы",
            tags=["ddl", "config"],
            expected_result={
                "mode": "model",
                "database": "quest_sandbox",
                "setup": ["CREATE SCHEMA podpolye"],
                "expect": [],
            },
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(
            sql_query="ALTER DATABASE quest_sandbox SET timezone TO 'UTC'; ALTER DATABASE quest_sandbox SET search_path TO podpolye, public"
        )
        result = await run_sql_query(
            mission_id=3,
            task_id=2,
            request=req,
            current_user=self.user,
            db=self.mock_db,
        )

        self.assertEqual(result["columns"], ["Статус операции"])
        self.assertEqual(
            result["data"],
            [["Команда успешно выполнена: ALTER DATABASE (симуляция завершена успешно)"]],
        )
        self.assertEqual(result["row_count"], 1)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_invalid_syntax_raises_400(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=84,
            mission_id=3,
            task_id=1,
            title="Создание схемы",
            tags=["ddl", "schema"],
            expected_result={"mode": "model", "setup": []},
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(sql_query="CREAT TABEL invalid_syntax")
        with self.assertRaises(HTTPException) as ctx:
            await run_sql_query(
                mission_id=3,
                task_id=1,
                request=req,
                current_user=self.user,
                db=self.mock_db,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Runtime error", ctx.exception.detail)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_forbidden_drop_database(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=84,
            mission_id=3,
            task_id=1,
            title="Создание схемы",
            tags=["ddl", "schema"],
            expected_result={"mode": "model", "setup": []},
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(sql_query="DROP DATABASE quest_sandbox")
        with self.assertRaises(HTTPException) as ctx:
            await run_sql_query(
                mission_id=3,
                task_id=1,
                request=req,
                current_user=self.user,
                db=self.mock_db,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("DROP DATABASE / ALTER SYSTEM запрещены", ctx.exception.detail)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_forbidden_alter_system(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=84,
            mission_id=3,
            task_id=1,
            title="Создание схемы",
            tags=["ddl", "schema"],
            expected_result={"mode": "model", "setup": []},
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(sql_query="ALTER SYSTEM SET max_connections = 100")
        with self.assertRaises(HTTPException) as ctx:
            await run_sql_query(
                mission_id=3,
                task_id=1,
                request=req,
                current_user=self.user,
                db=self.mock_db,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("DROP DATABASE / ALTER SYSTEM запрещены", ctx.exception.detail)

    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_run_empty_query(self, mock_repo_class, mock_log_event):
        task = SimpleNamespace(
            task_global_id=84,
            mission_id=3,
            task_id=1,
            title="Создание схемы",
            tags=["ddl", "schema"],
            expected_result={"mode": "model", "setup": []},
        )
        mock_repo = AsyncMock()
        mock_repo.get_task_info.return_value = task
        mock_repo_class.return_value = mock_repo

        req = SQLRequest(sql_query="   ")
        with self.assertRaises(HTTPException) as ctx:
            await run_sql_query(
                mission_id=3,
                task_id=1,
                request=req,
                current_user=self.user,
                db=self.mock_db,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Пустой запрос", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
