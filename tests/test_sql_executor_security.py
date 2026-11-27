import unittest
from fastapi import HTTPException
from src.utils.sql_executor import SQLExecutor


class TestSQLExecutorSecurity(unittest.TestCase):
    def setUp(self):
        # We don't need a live DB connection to test _validate_sql AST validation
        self.executor = SQLExecutor.__new__(SQLExecutor)

    def test_cte_delete_blocked(self):
        """CTE with DELETE statement must be blocked with 400."""
        query = "WITH pwned AS (DELETE FROM soldier RETURNING id) SELECT id FROM pwned;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_update=False)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("DELETE", ctx.exception.detail)

    def test_cte_update_blocked_when_allow_update_false(self):
        """CTE with UPDATE statement must be blocked when allow_update=False."""
        query = "WITH pwned AS (UPDATE soldier SET full_name = 'x' RETURNING id) SELECT id FROM pwned;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_update=False)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("UPDATE", ctx.exception.detail)

    def test_cte_insert_blocked(self):
        """CTE with INSERT statement must be blocked with 400."""
        query = "WITH pwned AS (INSERT INTO soldier (full_name) VALUES ('x') RETURNING id) SELECT id FROM pwned;"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query, allow_update=False)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("INSERT", ctx.exception.detail)

    def test_system_func_pg_read_file_blocked(self):
        """Calling pg_read_file must be blocked with 400."""
        query = "SELECT pg_read_file('/etc/passwd');"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("pg_read_file", ctx.exception.detail)

    def test_system_func_current_setting_blocked(self):
        """Calling current_setting must be blocked with 400."""
        query = "SELECT current_setting('config_file');"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("current_setting", ctx.exception.detail)

    def test_system_func_query_to_xml_blocked(self):
        """Calling query_to_xml must be blocked with 400."""
        query = "SELECT query_to_xml('SELECT 1', true, false, '');"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("query_to_xml", ctx.exception.detail)

    def test_system_func_dblink_blocked(self):
        """Calling dblink must be blocked with 400."""
        query = "SELECT dblink('dbname=postgres', 'SELECT 1');"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("dblink", ctx.exception.detail)

    def test_system_func_pg_sleep_allowed(self):
        """Calling pg_sleep is permitted as a safe utility function."""
        query = "SELECT pg_sleep(0.1);"
        # Should not raise exception
        self.executor._validate_sql(query)

    def test_system_func_qualified_name_blocked(self):
        """Calling pg_catalog.pg_read_file must also be blocked."""
        query = "SELECT pg_catalog.pg_read_file('/etc/passwd');"
        with self.assertRaises(HTTPException) as ctx:
            self.executor._validate_sql(query)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_legitimate_curriculum_queries_pass(self):
        """Verify that standard safe curriculum queries pass validation."""
        queries = [
            "SELECT unit_name FROM military_unit WHERE unit_name NOT LIKE '%стрелков%';",
            "SELECT item_name FROM equipment WHERE item_name LIKE '____';",
            """SELECT mu.unit_name, COUNT(ms.soldier_id)::int AS total_soldiers
               FROM military_unit mu
               JOIN military_service ms ON mu.id = ms.unit_id
               GROUP BY mu.unit_name
               ORDER BY mu.unit_name;""",
            """WITH stalingrad_artillery AS (
                   SELECT e.equipment_type, SUM(e.quantity) AS total_qty
                   FROM military_unit mu
                   JOIN equipment e ON mu.id = e.unit_id
                   WHERE mu.location = 'Сталинград' AND e.equipment_type = 'артиллерия'
                   GROUP BY e.equipment_type
               )
               SELECT equipment_type, total_qty FROM stalingrad_artillery;""",
            """SELECT s.full_name,
                      COUNT(DISTINCT b.id) AS battles_participated,
                      DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT b.id) DESC, s.full_name) AS hero_rank
               FROM soldier s
               JOIN military_service ms ON s.id = ms.soldier_id
               JOIN battle_military_unit bmu ON ms.unit_id = bmu.unit_id
               JOIN battle b ON bmu.battle_id = b.id
               WHERE ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
               GROUP BY s.full_name
               ORDER BY hero_rank
               LIMIT 20;""",
        ]
        for query in queries:
            try:
                self.executor._validate_sql(query)
            except HTTPException as e:
                self.fail(f"Legitimate query failed validation: {query}\nError: {e.detail}")

    def test_allow_update_flag(self):
        """When allow_update=True, UPDATE query without CTE should be accepted."""
        query = "UPDATE soldier SET full_name = 'Иванов Иван' WHERE id = 1;"
        # Should not raise exception when allow_update=True
        self.executor._validate_sql(query, allow_update=True)


if __name__ == "__main__":
    unittest.main()
