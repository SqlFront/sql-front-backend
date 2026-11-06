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

        users_mig2 = MIGRATIONS_DIR / "users_db" / "002_user_events_task_id_nullable.sql"
        self.assertTrue(users_mig2.exists(), "users_db migration 002 must exist")

        users_mig3 = MIGRATIONS_DIR / "users_db" / "003_fix_curriculum_duplicates.sql"
        self.assertTrue(users_mig3.exists(), "users_db migration 003 must exist")
        users3_content = users_mig3.read_text(encoding="utf-8")
        self.assertIn("003_fix_curriculum_duplicates.sql", users3_content)
        self.assertIn("Сезонность боевых действий", users3_content)
        self.assertIn("Критический дефицит снаряжения", users3_content)

        users_mig4 = MIGRATIONS_DIR / "users_db" / "004_feedback_fixes.sql"
        self.assertTrue(users_mig4.exists(), "users_db migration 004 must exist")
        users4_content = users_mig4.read_text(encoding="utf-8")
        self.assertIn("004_feedback_fixes.sql", users4_content)
        self.assertIn("Сила в единстве", users4_content)
        self.assertIn("Логистика Сталинградской битвы", users4_content)
        self.assertIn("Анализ эффективности частей", users4_content)
        self.assertIn("Логистика артиллерии Сталинградского фронта", users4_content)
        self.assertIn("Участники Сталинграда", users4_content)
        self.assertIn("Бойцы подразделения", users4_content)
        self.assertIn("task_global_id = 14", users4_content)
        self.assertIn("task_global_id = 37", users4_content)
        self.assertIn("task_global_id = 39", users4_content)
        self.assertIn("task_global_id = 41", users4_content)
        self.assertIn("task_global_id = 44", users4_content)
        self.assertIn("task_global_id = 107", users4_content)

        users_mig5 = MIGRATIONS_DIR / "users_db" / "005_fix_task_0_25.sql"
        self.assertTrue(users_mig5.exists(), "users_db migration 005 must exist")
        users5_content = users_mig5.read_text(encoding="utf-8")
        self.assertIn("005_fix_task_0_25.sql", users5_content)
        self.assertIn("Демография частей", users5_content)
        self.assertIn("task_global_id = 25", users5_content)
        self.assertIn("ORDER BY mu.unit_name", users5_content)

        users_mig6 = MIGRATIONS_DIR / "users_db" / "006_mission_3_clue_syntax.sql"
        self.assertTrue(users_mig6.exists(), "users_db migration 006 must exist")
        users6_content = users_mig6.read_text(encoding="utf-8")
        self.assertIn("006_mission_3_clue_syntax.sql", users6_content)
        self.assertIn("ALTER DATABASE <имя> SET <параметр> TO <значение>", users6_content)
        self.assertIn("task_global_id = 85", users6_content)

        users_mig7 = MIGRATIONS_DIR / "users_db" / "007_standardize_output_columns.sql"
        self.assertTrue(users_mig7.exists(), "users_db migration 007 must exist")
        users7_content = users_mig7.read_text(encoding="utf-8")
        self.assertIn("007_standardize_output_columns.sql", users7_content)
        self.assertIn("task_global_id = 1", users7_content)

        game_mig2 = MIGRATIONS_DIR / "game_db" / "002_battle_military_unit.sql"
        self.assertTrue(game_mig2.exists(), "game_db migration 002 must exist")
        game2_content = game_mig2.read_text(encoding="utf-8")
        self.assertIn("battle_military_unit", game2_content)

        users_mig8 = MIGRATIONS_DIR / "users_db" / "008_fix_mission_2_and_task_1_3.sql"
        self.assertTrue(users_mig8.exists(), "users_db migration 008 must exist")
        users8_content = users_mig8.read_text(encoding="utf-8")
        self.assertIn("battle_military_unit", users8_content)

        users_mig9 = MIGRATIONS_DIR / "users_db" / "009_compact_output_column_hints.sql"
        self.assertTrue(users_mig9.exists(), "users_db migration 009 must exist")
        users9_content = users_mig9.read_text(encoding="utf-8")
        self.assertIn("Поля в результирующей таблице:", users9_content)


        users_mig10 = MIGRATIONS_DIR / "users_db" / "010_fix_tasks_1_9_and_1_23.sql"
        self.assertTrue(users_mig10.exists(), "users_db migration 010 must exist")
        users10_content = users_mig10.read_text(encoding="utf-8")
        self.assertIn("010_fix_tasks_1_9_and_1_23.sql", users10_content)
        self.assertIn("task_global_id = 41", users10_content)
        self.assertIn("task_global_id = 51", users10_content)
        self.assertIn("stalingrad_artillery", users10_content)
        self.assertIn("battle_military_unit", users10_content)

        users_mig11 = MIGRATIONS_DIR / "users_db" / "011_add_user_query_to_tasks_solved.sql"
        self.assertTrue(users_mig11.exists(), "users_db migration 011 must exist")
        users11_content = users_mig11.read_text(encoding="utf-8")
        self.assertIn("011_add_user_query_to_tasks_solved.sql", users11_content)
        self.assertIn("tasks_solved", users11_content)
        self.assertIn("user_query", users11_content)
        self.assertIn("updated_at", users11_content)

        users_mig12 = MIGRATIONS_DIR / "users_db" / "012_fix_tasks_2_11_and_2_12.sql"
        self.assertTrue(users_mig12.exists(), "users_db migration 012 must exist")
        users12_content = users_mig12.read_text(encoding="utf-8")
        self.assertIn("012_fix_tasks_2_11_and_2_12.sql", users12_content)
        self.assertIn("task_global_id = 83", users12_content)
        self.assertIn("task_global_id = 62", users12_content)
        self.assertIn("FMMonth", users12_content)
        self.assertIn("battle_units", users12_content)

if __name__ == "__main__":
    unittest.main()
