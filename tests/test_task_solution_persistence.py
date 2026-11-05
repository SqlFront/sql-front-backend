import pytest
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from datetime import datetime

from src.models.task import Task, TaskSolved
from src.schemas.task import TaskInfo, TaskWithStatusResponse, SQLRequest
from src.repositories.task import TaskRepository
from src.api.task import get_task_info, submit_sql_query


class TestTaskModelAndSchemas(unittest.TestCase):
    def test_task_solved_model_attributes(self):
        """Проверяем, что в модели TaskSolved есть атрибуты user_query и updated_at."""
        self.assertTrue(hasattr(TaskSolved, "user_query"))
        self.assertTrue(hasattr(TaskSolved, "updated_at"))
        self.assertTrue(hasattr(TaskSolved, "solved_at"))

    def test_task_schemas_user_solution_field(self):
        """Проверяем, что схемы TaskInfo и TaskWithStatusResponse содержат user_solution."""
        info = TaskInfo(
            mission_id=1,
            task_id=2,
            task_global_id=10,
            title="Тестовая задача",
            description="Описание",
            is_solved=True,
            user_solution="SELECT 42;",
        )
        self.assertEqual(info.user_solution, "SELECT 42;")

        response = TaskWithStatusResponse(
            task_id=2,
            mission_id=1,
            title="Тестовая задача",
            description="Описание",
            is_solved=True,
            has_clue1=False,
            has_clue2=False,
            previous={},
            next={},
            user_solution="SELECT 42;",
        )
        self.assertEqual(response.user_solution, "SELECT 42;")


class TestTaskRepositorySolutionPersistence(unittest.IsolatedAsyncioTestCase):
    async def test_add_solved_task_insert_new(self):
        """Проверяем создание новой записи с user_query."""
        session = AsyncMock()
        session.add = MagicMock()
        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = None
        session.execute.return_value = execute_result

        repo = TaskRepository(session)
        result = await repo.add_solved_task(
            user_id=10, task_id=25, user_query="SELECT * FROM soldiers;"
        )

        session.add.assert_called_once()
        added_obj = session.add.call_args[0][0]
        self.assertIsInstance(added_obj, TaskSolved)
        self.assertEqual(added_obj.user_id, 10)
        self.assertEqual(added_obj.task_global_id, 25)
        self.assertEqual(added_obj.user_query, "SELECT * FROM soldiers;")
        self.assertIsNotNone(added_obj.updated_at)
        session.commit.assert_awaited_once()
        self.assertEqual(result, added_obj)

    async def test_add_solved_task_upsert_existing(self):
        """Проверяем обновление существующей записи (upsert) с обновлением user_query и updated_at."""
        session = AsyncMock()
        session.add = MagicMock()
        existing = TaskSolved(
            user_id=10,
            task_global_id=25,
            solved_at=datetime(2026, 1, 1),
            user_query="SELECT 1;",
            updated_at=datetime(2026, 1, 1),
        )
        execute_result = MagicMock()
        execute_result.scalars.return_value.first.return_value = existing
        session.execute.return_value = execute_result

        repo = TaskRepository(session)
        result = await repo.add_solved_task(
            user_id=10, task_id=25, user_query="SELECT 2;"
        )

        session.add.assert_not_called()
        self.assertEqual(existing.user_query, "SELECT 2;")
        self.assertGreater(existing.updated_at, datetime(2026, 1, 1))
        session.commit.assert_awaited_once()
        self.assertEqual(result, existing)

    async def test_get_task_info_with_status_solved(self):
        """Проверяем получение задачи с решением, когда задача решена."""
        session = AsyncMock()
        fake_task = Task(task_id=1, mission_id=0, task_global_id=5, title="T1")
        fake_solved = TaskSolved(
            user_id=1,
            task_global_id=5,
            user_query="SELECT title FROM missions;",
        )

        res1 = MagicMock()
        res1.scalars.return_value.first.return_value = fake_task
        res2 = MagicMock()
        res2.scalars.return_value.first.return_value = fake_solved
        session.execute.side_effect = [res1, res2]

        repo = TaskRepository(session)
        task, is_solved, user_solution = await repo.get_task_info_with_status(0, 1, 1)

        self.assertEqual(task, fake_task)
        self.assertTrue(is_solved)
        self.assertEqual(user_solution, "SELECT title FROM missions;")

    async def test_get_task_info_with_status_not_solved(self):
        """Проверяем получение задачи, когда задача еще не решена."""
        session = AsyncMock()
        fake_task = Task(task_id=1, mission_id=0, task_global_id=5, title="T1")

        res1 = MagicMock()
        res1.scalars.return_value.first.return_value = fake_task
        res2 = MagicMock()
        res2.scalars.return_value.first.return_value = None
        session.execute.side_effect = [res1, res2]

        repo = TaskRepository(session)
        task, is_solved, user_solution = await repo.get_task_info_with_status(0, 1, 1)

        self.assertEqual(task, fake_task)
        self.assertFalse(is_solved)
        self.assertIsNone(user_solution)

    async def test_get_task_by_id(self):
        """Проверяем метод get_task_by_id."""
        session = AsyncMock()
        fake_task = Task(task_id=1, mission_id=0, task_global_id=5, title="T1")
        fake_solved = TaskSolved(
            user_id=1,
            task_global_id=5,
            user_query="SELECT 100;",
        )

        res1 = MagicMock()
        res1.scalars.return_value.first.return_value = fake_task
        res2 = MagicMock()
        res2.scalars.return_value.first.return_value = fake_solved
        session.execute.side_effect = [res1, res2]

        repo = TaskRepository(session)
        task, is_solved, user_solution = await repo.get_task_by_id(5, user_id=1)

        self.assertEqual(task, fake_task)
        self.assertTrue(is_solved)
        self.assertEqual(user_solution, "SELECT 100;")


class TestTaskApiSolutionPersistence(unittest.IsolatedAsyncioTestCase):
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    @patch("src.api.task.TaskRepository")
    async def test_get_task_info_endpoint_returns_user_solution(
        self, mock_repo_class, mock_log
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        fake_task = SimpleNamespace(
            task_id=3,
            mission_id=1,
            task_global_id=40,
            title="Задача 3",
            description="Описание задачи",
            tags=["medium"],
        )
        mock_repo.get_task_info_with_status = AsyncMock(
            return_value=(fake_task, True, "SELECT id FROM tank;")
        )
        mock_repo.session = MagicMock()
        clue_result = MagicMock()
        clue_result.scalar_one_or_none.return_value = None
        mock_repo.session.execute = AsyncMock(return_value=clue_result)
        mock_repo.find_prev_task_data = AsyncMock(return_value=(1, 2))
        mock_repo.find_next_task_data = AsyncMock(return_value=(1, 4))

        current_user = SimpleNamespace(user_id=42, total_score=200)
        db_session = AsyncMock()

        result = await get_task_info(
            mission_id=1,
            task_id=3,
            current_user=current_user,
            db=db_session,
        )

        self.assertEqual(result["user_solution"], "SELECT id FROM tank;")
        self.assertTrue(result["is_solved"])

    @patch("src.api.task.sql_executor")
    @patch("src.api.task.TaskRepository")
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    async def test_submit_sql_query_persists_user_solution_on_correct(
        self, mock_log, mock_repo_class, mock_sql_executor
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_task_info = AsyncMock(
            return_value=SimpleNamespace(
                task_global_id=15,
                expected_result={"data": [["Alpha"]]},
            )
        )
        mock_sql_executor.execute_sql = AsyncMock(
            return_value={"columns": ["name"], "data": [["Alpha"]]}
        )
        mock_repo.check_and_reward_task = AsyncMock(
            return_value={
                "was_solved_before": False,
                "points_earned": 50,
                "points_penalty": 0,
                "message": "Правильно! Заработано 50 баллов",
                "awarded_achievements": [],
                "current_points": 250,
            }
        )
        mock_repo.add_solved_task = AsyncMock()

        current_user = SimpleNamespace(user_id=7, total_score=200)
        db_session = AsyncMock()

        submitted_query = "SELECT name FROM units WHERE id = 1;"
        result = await submit_sql_query(
            mission_id=0,
            task_id=5,
            request=SQLRequest(sql_query=submitted_query),
            current_user=current_user,
            db=db_session,
        )

        self.assertTrue(result["is_correct"])
        mock_repo.add_solved_task.assert_awaited_once_with(
            user_id=7,
            task_id=15,
            user_query=submitted_query,
        )

    @patch("src.api.task.sql_executor")
    @patch("src.api.task.TaskRepository")
    @patch("src.api.task.log_user_event", new_callable=AsyncMock)
    async def test_submit_sql_query_does_not_persist_on_incorrect(
        self, mock_log, mock_repo_class, mock_sql_executor
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_task_info = AsyncMock(
            return_value=SimpleNamespace(
                task_global_id=15,
                expected_result={"data": [["Alpha"]]},
            )
        )
        mock_sql_executor.execute_sql = AsyncMock(
            return_value={"columns": ["name"], "data": [["Beta"]]}
        )
        mock_repo.check_and_reward_task = AsyncMock(
            return_value={
                "was_solved_before": False,
                "points_earned": 0,
                "points_penalty": 10,
                "message": "Ответ неверный!",
                "awarded_achievements": [],
                "current_points": 190,
            }
        )
        mock_repo.add_solved_task = AsyncMock()

        current_user = SimpleNamespace(user_id=7, total_score=200)
        db_session = AsyncMock()

        result = await submit_sql_query(
            mission_id=0,
            task_id=5,
            request=SQLRequest(sql_query="SELECT name FROM units;"),
            current_user=current_user,
            db=db_session,
        )

        self.assertFalse(result["is_correct"])
        mock_repo.add_solved_task.assert_not_called()
