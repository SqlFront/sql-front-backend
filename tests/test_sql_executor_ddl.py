import unittest
from fastapi import HTTPException
from src.utils.sql_executor import SQLExecutor


class TestSQLExecutorDDLValidation(unittest.TestCase):
    def setUp(self):
        # We don't connect to the DB in unit test for _validate_sql
        self.executor = SQLExecutor.__new__(SQLExecutor)

    def test_ddl_disallowed_by_default(self):
        query = "CREATE OR REPLACE FUNCTION test_func() RETURNS INT AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=False)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_ddl_allowed_function(self):
        query = "CREATE OR REPLACE FUNCTION get_enlistment_age(p_soldier_id INT) RETURNS INT AS $$ BEGIN RETURN 18; END; $$ LANGUAGE plpgsql;"
        # Should not raise exception
        self.executor._validate_sql(query, allow_ddl=True)

    def test_ddl_allowed_procedure(self):
        query = "CREATE OR REPLACE PROCEDURE transfer_soldier(p_soldier_id INT, p_new_unit_id INT) AS $$ BEGIN UPDATE military_service SET unit_id = p_new_unit_id WHERE soldier_id = p_soldier_id; END; $$ LANGUAGE plpgsql;"
        # Should not raise exception
        self.executor._validate_sql(query, allow_ddl=True)

    def test_ddl_allowed_trigger(self):
        query = "CREATE TRIGGER after_equipment_insert AFTER INSERT ON equipment FOR EACH ROW EXECUTE FUNCTION log_equipment();"
        # Should not raise exception
        self.executor._validate_sql(query, allow_ddl=True)

    def test_ddl_forbidden_system_table(self):
        query = "CREATE OR REPLACE FUNCTION leak() RETURNS INT AS $$ BEGIN SELECT * FROM pg_shadow; RETURN 1; END; $$ LANGUAGE plpgsql;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=True)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_ddl_forbidden_drop_database(self):
        query = "DROP DATABASE game_db;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_ddl=True)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_reveal_expected_ddl(self):
        from src.api.task import _reveal_expected
        from types import SimpleNamespace
        task = SimpleNamespace(expected_result={
            "mode": "ddl",
            "columns": ["age"],
            "data": [[18]],
            "test_query": "SELECT 18;"
        })
        revealed = _reveal_expected(task)
        self.assertEqual(revealed["columns"], ["age"])
        self.assertEqual(revealed["data"], [[18]])




class TestCatalogModelMultilineDDL(unittest.TestCase):
    def test_split_statements_alter_database_without_semicolon(self):
        from src.utils.catalog_model import split_statements
        sql = (
            "alter database quest_sandbox set timezone to 'UTC'\n"
            "alter database quest_sandbox set search_path to podpolye, public"
        )
        stmts = split_statements(sql)
        self.assertEqual(len(stmts), 2)
        self.assertEqual(stmts[0], "alter database quest_sandbox set timezone to 'UTC'")
        self.assertEqual(stmts[1], "alter database quest_sandbox set search_path to podpolye, public")

    def test_verify_multiline_ddl_without_semicolon(self):
        from src.utils.catalog_model import verify
        spec = {
            "mode": "model",
            "setup": ["CREATE SCHEMA podpolye"],
            "expect": [
                {
                    "args": {"db": "quest_sandbox"},
                    "probe": "db_settings",
                    "title": "настройки базы",
                    "value": [["search_path", "podpolye,public"], ["timezone", "UTC"]],
                },
                {
                    "args": {"name": "podpolye"},
                    "probe": "schema_exists",
                    "title": "схема на месте",
                    "value": True,
                },
            ],
            "reveal": "Что проверяется: настройки базы; схема на месте.",
        }
        student_sql = (
            "alter database quest_sandbox set timezone to 'UTC'\n"
            "alter database quest_sandbox set search_path to podpolye, public"
        )
        ok, msg = verify(student_sql, spec)
        self.assertTrue(ok, f"Expected verify() to succeed, got: {msg}")

    def test_split_preserves_parentheses_and_literals(self):
        from src.utils.catalog_model import split_statements
        # Parentheses with newlines inside should not split
        table_sql = (
            "CREATE TABLE podpolye.depots (\n"
            "    depot_id integer PRIMARY KEY,\n"
            "    depot_name varchar(50) NOT NULL\n"
            ")\n"
            "CREATE TABLE podpolye.items (\n"
            "    item_id integer PRIMARY KEY\n"
            ")"
        )
        stmts = split_statements(table_sql)
        self.assertEqual(len(stmts), 2)
        self.assertIn("depot_id integer PRIMARY KEY", stmts[0])
        self.assertIn("item_id integer PRIMARY KEY", stmts[1])

        # String literals with newlines and statement keywords should not split
        comment_sql = (
            "COMMENT ON TABLE podpolye.depots IS 'Line 1\n"
            "CREATE TABLE fake_inside_string (id int)\n"
            "Line 3';"
        )
        stmts = split_statements(comment_sql)
        self.assertEqual(len(stmts), 1)

        # Dollar quoted body with newlines should not split
        func_sql = (
            "CREATE FUNCTION test_fn() RETURNS void AS $$\n"
            "BEGIN\n"
            "    ALTER TABLE t ADD COLUMN c int;\n"
            "END;\n"
            "$$ LANGUAGE plpgsql;"
        )
        stmts = split_statements(func_sql)
        self.assertEqual(len(stmts), 1)

        # Multi-line ALTER TABLE subclauses (ALTER COLUMN / DROP CONSTRAINT) should not split
        alter_sql = (
            "ALTER TABLE podpolye.depots\n"
            "    ALTER COLUMN depot_name DROP NOT NULL"
        )
        stmts = split_statements(alter_sql)
        self.assertEqual(len(stmts), 1)


if __name__ == "__main__":
    unittest.main()
