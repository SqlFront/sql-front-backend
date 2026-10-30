import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace
from fastapi import HTTPException
from src.api.task import submit_sql_query
from src.schemas.task import SQLRequest


class TestSubmitSQLQueryErrorHandling(unittest.IsolatedAsyncioTestCase):
    @patch("src.api.task.sql_executor")
    @patch("src.api.task.TaskRepository")
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    async def test_invalid_sql_returns_not_correct_without_500(
        self, mock_log_event, mock_repo_class, mock_sql_executor
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # Fake task
        mock_repo.get_task_info = AsyncMock(return_value=SimpleNamespace(
            task_global_id=1,
            expected_result={"data": [["some_data"]]}
        ))
        
        # When user submits a broken SQL, execute_sql throws HTTPException(400)
        mock_sql_executor.execute_sql = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="Ошибка синтаксиса: syntax error at or near 'SELEC'")
        )
        
        mock_repo.check_and_reward_task = AsyncMock(return_value={
            "was_solved_before": False,
            "points_earned": 0,
            "points_penalty": 10,
            "message": "Ответ неверный! Списано 10 баллов",
            "awarded_achievements": [],
            "current_points": 90,
        })
        
        current_user = SimpleNamespace(user_id=1, total_score=100)
        db_session = AsyncMock()
        
        result = await submit_sql_query(
            mission_id=0,
            task_id=1,
            request=SQLRequest(sql_query="SELEC * FROM table"),
            current_user=current_user,
            db=db_session,
        )
        
        self.assertFalse(result["is_correct"])
        self.assertEqual(result["hint"], "Ошибка синтаксиса: syntax error at or near 'SELEC'")
        self.assertEqual(result["points_penalty"], 10)
        mock_repo.check_and_reward_task.assert_awaited_once_with(
            user_id=1,
            mission_id=0,
            task_id=1,
            is_correct=False,
        )


if __name__ == "__main__":
    unittest.main()
