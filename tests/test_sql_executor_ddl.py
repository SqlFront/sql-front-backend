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




class TestCatalogModelTypeEquivalenceAndSerial(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "mode": "model",
            "setup": ["CREATE SCHEMA podpolye"],
            "expect": [
                {
                    "args": {"table": "podpolye.depots"},
                    "probe": "columns",
                    "title": "столбцы таблицы складов",
                    "value": [
                        ["depot_id", "integer", None, True, False],
                        ["depot_name", "character varying", 40, True, False],
                        ["sector", "character", 1, True, False],
                        ["capacity_t", "integer", None, False, False],
                    ],
                },
                {
                    "args": {"table": "podpolye.depots"},
                    "probe": "primary_key",
                    "title": "первичный ключ складов",
                    "value": ["depot_id"],
                },
            ],
            "reveal": "Что проверяется: столбцы таблицы складов; первичный ключ складов.",
        }

    def test_verify_integer_primary_key(self):
        from src.utils.catalog_model import verify
        sql = (
            "CREATE TABLE podpolye.depots(\n"
            "    depot_id integer PRIMARY KEY,\n"
            "    depot_name varchar(40) NOT NULL,\n"
            "    sector char(1) NOT NULL,\n"
            "    capacity_t integer\n"
            ");"
        )
        ok, msg = verify(sql, self.spec)
        self.assertTrue(ok, f"Expected verify() with INTEGER PRIMARY KEY to pass, got: {msg}")

    def test_verify_serial_primary_key(self):
        from src.utils.catalog_model import verify
        sql = (
            "CREATE TABLE podpolye.depots(\n"
            "    depot_id serial PRIMARY KEY,\n"
            "    depot_name varchar(40) NOT NULL,\n"
            "    sector char(1) NOT NULL,\n"
            "    capacity_t integer\n"
            ");"
        )
        ok, msg = verify(sql, self.spec)
        self.assertTrue(ok, f"Expected verify() with SERIAL PRIMARY KEY to pass, got: {msg}")

    def test_verify_int_and_int4_primary_key(self):
        from src.utils.catalog_model import verify
        for type_name in ("int", "int4"):
            sql = (
                f"CREATE TABLE podpolye.depots(\n"
                f"    depot_id {type_name} PRIMARY KEY,\n"
                f"    depot_name varchar(40) NOT NULL,\n"
                f"    sector char(1) NOT NULL,\n"
                f"    capacity_t integer\n"
                f");"
            )
            ok, msg = verify(sql, self.spec)
            self.assertTrue(ok, f"Expected verify() with {type_name} PRIMARY KEY to pass, got: {msg}")

    def test_verify_smallserial_and_smallint_primary_key(self):
        from src.utils.catalog_model import verify
        for type_name in ("smallserial", "smallint"):
            sql = (
                f"CREATE TABLE podpolye.depots(\n"
                f"    depot_id {type_name} PRIMARY KEY,\n"
                f"    depot_name varchar(40) NOT NULL,\n"
                f"    sector char(1) NOT NULL,\n"
                f"    capacity_t integer\n"
                f");"
            )
            ok, msg = verify(sql, self.spec)
            self.assertTrue(ok, f"Expected verify() with {type_name} PRIMARY KEY to pass, got: {msg}")

    def test_verify_bigint_spec_equivalences(self):
        from src.utils.catalog_model import verify
        bigint_spec = {
            "mode": "model",
            "setup": ["CREATE SCHEMA podpolye"],
            "expect": [
                {
                    "args": {"table": "podpolye.events"},
                    "probe": "columns",
                    "title": "столбцы таблицы событий",
                    "value": [
                        ["id", "bigint", None, True, False],
                        ["title", "text", None, True, False],
                    ],
                },
                {
                    "args": {"table": "podpolye.events"},
                    "probe": "primary_key",
                    "title": "первичный ключ",
                    "value": ["id"],
                },
            ],
        }
        for type_name in ("bigint", "bigserial", "int8"):
            sql = f"CREATE TABLE podpolye.events(id {type_name} PRIMARY KEY, title text NOT NULL);"
            ok, msg = verify(sql, bigint_spec)
            self.assertTrue(ok, f"Expected verify() with {type_name} to pass for bigint spec, got: {msg}")

    def test_verify_incompatible_type_rejected(self):
        from src.utils.catalog_model import verify
        sql = (
            "CREATE TABLE podpolye.depots(\n"
            "    depot_id text PRIMARY KEY,\n"
            "    depot_name varchar(40) NOT NULL,\n"
            "    sector char(1) NOT NULL,\n"
            "    capacity_t integer\n"
            ");"
        )
        ok, msg = verify(sql, self.spec)
        self.assertFalse(ok, "Expected verify() with text PRIMARY KEY to fail when integer is expected")

    def test_verify_explicit_default_without_serial_rejected(self):
        from src.utils.catalog_model import verify
        sql = (
            "CREATE TABLE podpolye.depots(\n"
            "    depot_id integer DEFAULT 42 PRIMARY KEY,\n"
            "    depot_name varchar(40) NOT NULL,\n"
            "    sector char(1) NOT NULL,\n"
            "    capacity_t integer\n"
            ");"
        )
        ok, msg = verify(sql, self.spec)
        self.assertFalse(ok, "Expected verify() with unexpected explicit DEFAULT to fail")

    def test_types_compatible_helper(self):
        from src.utils.catalog_model import types_compatible
        # Integer group
        for t in ("integer", "int", "serial", "int4", "smallserial", "smallint", "int2"):
            self.assertTrue(types_compatible(t, "integer"))
            self.assertTrue(types_compatible(t, "int"))
        # Bigint group
        for t in ("bigint", "bigserial", "int8"):
            self.assertTrue(types_compatible(t, "bigint"))
            self.assertTrue(types_compatible(t, "int8"))
        # Incompatibilities
        self.assertFalse(types_compatible("bigint", "integer"))
        self.assertFalse(types_compatible("integer", "bigint"))
        self.assertFalse(types_compatible("text", "integer"))


if __name__ == "__main__":
    unittest.main()
