import unittest
from pathlib import Path

from src.migrations.runner import to_asyncpg_dsn, MIGRATIONS_DIR


class TestMigrations(unittest.TestCase):
    def test_to_asyncpg_dsn_conversion(self):
        url = "postgresql+asyncpg://postgres:secret@postgres:5432/users_db"
        dsn = to_asyncpg_dsn(url)
        self.assertEqual(dsn, "postgresql://postgres:secret@postgres:5432/users_db")

    def test_to_asyncpg_dsn_swap_db(self):
        url = "postgresql+asyncpg://postgres:secret@postgres:5432/users_db"
        dsn = to_asyncpg_dsn(url, db_name="game_db")
        self.assertEqual(dsn, "postgresql://postgres:secret@postgres:5432/game_db")

    def test_migration_files_exist_and_non_empty(self):
        users_mig = MIGRATIONS_DIR / "users_db" / "001_sync_tasks_and_tables.sql"
        game_mig = MIGRATIONS_DIR / "game_db" / "001_equipment_audit.sql"

        self.assertTrue(users_mig.exists(), "users_db migration 001 must exist")
        self.assertTrue(game_mig.exists(), "game_db migration 001 must exist")

        users_content = users_mig.read_text(encoding="utf-8")
        self.assertIn("public.tasks", users_content)
        self.assertIn("quest_tasks_solved", users_content)
        self.assertIn("ON CONFLICT (task_global_id)", users_content)
        # Check task 63 fix
        self.assertIn("3-я воздушная армия", users_content)

        game_content = game_mig.read_text(encoding="utf-8")
        self.assertIn("equipment_audit", game_content)

        users_mig2 = MIGRATIONS_DIR / "users_db" / "002_fix_curriculum_duplicates.sql"
        self.assertTrue(users_mig2.exists(), "users_db migration 002 must exist")
        users2_content = users_mig2.read_text(encoding="utf-8")
        self.assertIn("002_fix_curriculum_duplicates.sql", users2_content)
        self.assertIn("Сезонность боевых действий", users2_content)
        self.assertIn("Критический дефицит снаряжения", users2_content)


if __name__ == "__main__":
    unittest.main()
