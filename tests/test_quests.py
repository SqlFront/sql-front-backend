import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from fastapi import HTTPException

from src.api.quests import sanitize_quest_query, _extract_update_value, run_quest_sql, submit_quest_solution
from src.schemas.quest import QuestRunRequest, QuestSubmitRequest
from src.utils.sql_executor import SQLExecutor


class TestSanitizeQuestQuery(unittest.TestCase):
    def test_semicolon_at_end(self):
        self.assertEqual(sanitize_quest_query("SELECT id FROM map;"), "SELECT id FROM map")

    def test_semicolon_with_trailing_spaces(self):
        self.assertEqual(sanitize_quest_query("SELECT id FROM map ; "), "SELECT id FROM map")

    def test_semicolon_with_newlines_and_tabs(self):
        self.assertEqual(sanitize_quest_query("SELECT id FROM map ;\n\r\t"), "SELECT id FROM map")

    def test_multiple_semicolons_and_spaces(self):
        self.assertEqual(sanitize_quest_query("SELECT id FROM map ; ; ; "), "SELECT id FROM map")

    def test_update_with_semicolon(self):
        self.assertEqual(sanitize_quest_query("UPDATE decision SET result = 1;"), "UPDATE decision SET result = 1")

    def test_update_with_semicolon_and_spaces(self):
        self.assertEqual(sanitize_quest_query("UPDATE decision SET result = 1 ;  \n"), "UPDATE decision SET result = 1")

    def test_semicolon_inside_string_literal_preserved(self):
        self.assertEqual(
            sanitize_quest_query("SELECT * FROM map WHERE status = 'semi;colon'; "),
            "SELECT * FROM map WHERE status = 'semi;colon'",
        )

    def test_empty_or_none(self):
        self.assertEqual(sanitize_quest_query(""), "")
        self.assertEqual(sanitize_quest_query(None), "")
        self.assertEqual(sanitize_quest_query("   \n\t; ; "), "")


class TestExtractUpdateValue(unittest.TestCase):
    def test_integer_value(self):
        self.assertEqual(_extract_update_value("UPDATE decision SET result = 1;"), "1")

    def test_integer_value_trailing_spaces(self):
        self.assertEqual(_extract_update_value("UPDATE decision SET result = 1 ; "), "1")

    def test_single_quoted_string(self):
        self.assertEqual(_extract_update_value("UPDATE decision SET result = '1';"), "1")

    def test_single_quoted_string_with_spaces(self):
        self.assertEqual(_extract_update_value("UPDATE decision SET result = '1' ; "), "1")

    def test_double_quoted_string(self):
        self.assertEqual(_extract_update_value('UPDATE decision SET result = "1";'), "1")

    def test_double_quoted_with_spaces(self):
        self.assertEqual(_extract_update_value('UPDATE decision SET result = "2" ; '), "2")

    def test_two_digit_number(self):
        self.assertEqual(_extract_update_value("UPDATE decision_factory SET result = 10;"), "10")

    def test_with_where_clause(self):
        self.assertEqual(_extract_update_value("UPDATE decision SET result = 2 WHERE 1=1;"), "2")

    def test_string_with_where_clause(self):
        self.assertEqual(
            _extract_update_value("UPDATE items SET assigned_to = 'Sasha' WHERE weight <= 2;"),
            "Sasha",
        )

    def test_string_with_double_quotes_and_where(self):
        self.assertEqual(
            _extract_update_value('UPDATE items SET assigned_to = "Grisha" WHERE weight > 2;'),
            "Grisha",
        )

    def test_non_update_returns_empty(self):
        self.assertEqual(_extract_update_value("SELECT * FROM map;"), "")


class TestSQLExecutorSanitize(unittest.TestCase):
    def test_clean_query_static_method(self):
        self.assertEqual(SQLExecutor._clean_query("SELECT 1 ; "), "SELECT 1")
        self.assertEqual(SQLExecutor._clean_query("SELECT 1;\n"), "SELECT 1")
        self.assertEqual(SQLExecutor._clean_query(""), "")
        self.assertEqual(SQLExecutor._clean_query(None), "")


class TestQuestEndpoints(unittest.IsolatedAsyncioTestCase):
    @patch("src.api.quests.sql_executor")
    async def test_run_quest_sql_sanitizes_query(self, mock_sql_executor):
        mock_repo = MagicMock()
        mock_repo.get_user_current_scene = AsyncMock(return_value={
            "scene_id": "chapter_1",
            "is_branching": False,
        })
        mock_sql_executor.execute_sql = AsyncMock(return_value={"columns": ["id"], "data": [[1]], "row_count": 1})

        user = SimpleNamespace(user_id=1)
        req = QuestRunRequest(scene_id="chapter_1", sql_query="SELECT id FROM map ; \n")

        res = await run_quest_sql("hope", req, user, mock_repo)
        self.assertEqual(res["row_count"], 1)
        mock_sql_executor.execute_sql.assert_awaited_once_with("SELECT id FROM map", allow_star=True)

    async def test_run_quest_sql_branching_scene_forbidden(self):
        mock_repo = MagicMock()
        mock_repo.get_user_current_scene = AsyncMock(return_value={
            "scene_id": "chapter_4",
            "is_branching": True,
        })

        user = SimpleNamespace(user_id=1)
        req = QuestRunRequest(scene_id="chapter_4", sql_query="UPDATE decision SET result = 1;")

        with self.assertRaises(HTTPException) as ctx:
            await run_quest_sql("hope", req, user, mock_repo)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Пока низя", ctx.exception.detail)

    @patch("src.api.quests.sql_executor")
    @patch("src.api.quests.ScoringService")
    async def test_submit_quest_solution_select_star_allowed(self, mock_scoring_cls, mock_sql_executor):
        mock_repo = MagicMock()
        mock_repo.is_task_solved = AsyncMock(return_value=False)
        mock_repo.get_user_current_scene = AsyncMock(return_value={
            "scene_id": "chapter_1",
            "is_branching": False,
            "expected_result": {
                "columns": ["id"],
                "data": [[1]],
            },
        })
        mock_repo.submit_answer = AsyncMock(return_value={"status": "success"})
        mock_repo.mark_task_solved = AsyncMock()

        mock_scoring = MagicMock()
        mock_scoring.add_points = AsyncMock()
        mock_scoring_cls.return_value = mock_scoring

        mock_sql_executor.execute_sql = AsyncMock(return_value={
            "columns": ["id"],
            "data": [[1]],
            "row_count": 1,
        })

        user = SimpleNamespace(user_id=1)
        db_mock = AsyncMock()
        db_mock.add = MagicMock()
        req = QuestSubmitRequest(scene_id="chapter_1", sql_query="SELECT * FROM map WHERE id = 1 ; ")

        res = await submit_quest_solution("hope", req, user, mock_repo, db_mock)
        self.assertTrue(res["is_correct"])
        mock_sql_executor.execute_sql.assert_awaited_once_with(
            "SELECT * FROM map WHERE id = 1", allow_star=True
        )

    @patch("src.api.quests.sql_executor")
    @patch("src.api.quests.ScoringService")
    async def test_submit_quest_solution_branching_with_semicolon(self, mock_scoring_cls, mock_sql_executor):
        mock_repo = MagicMock()
        mock_repo.is_task_solved = AsyncMock(return_value=False)
        mock_repo.get_user_current_scene = AsyncMock(return_value={
            "scene_id": "chapter_4",
            "is_branching": True,
            "branches": {
                "1": "chapter_5_1",
                "2": "chapter_5_2_1",
            },
            "expected_result": {
                "query_type": "UPDATE",
                "target_table": "decision",
                "target_column": "result",
            },
        })
        mock_repo.submit_answer = AsyncMock(return_value={"status": "success"})
        mock_repo.mark_task_solved = AsyncMock()

        mock_scoring = MagicMock()
        mock_scoring.add_points = AsyncMock()
        mock_scoring_cls.return_value = mock_scoring

        mock_sql_executor.simulate_update = AsyncMock(return_value=1)

        user = SimpleNamespace(user_id=1)
        db_mock = AsyncMock()
        db_mock.add = MagicMock()
        req = QuestSubmitRequest(scene_id="chapter_4", sql_query="UPDATE decision SET result = 1 ;  ")

        res = await submit_quest_solution("hope", req, user, mock_repo, db_mock)
        self.assertTrue(res["is_correct"])
        mock_sql_executor.simulate_update.assert_awaited_once_with(
            "UPDATE decision SET result = 1", allowed_tables=["decision"]
        )
        mock_repo.submit_answer.assert_awaited_once_with(
            user_id=1,
            quest_id="hope",
            user_answer="1",
            is_correct=True,
        )


if __name__ == "__main__":
    unittest.main()
