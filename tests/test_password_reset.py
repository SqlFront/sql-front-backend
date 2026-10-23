import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from src.schemas.user import PasswordResetRequest
from src.repositories.user import UserRepository
from src.api.auth import reset_password


class TestPasswordResetSchema(unittest.TestCase):
    def test_valid_payload(self):
        req = PasswordResetRequest(
            login="student1",
            email="student1@example.com",
            new_password="newsecret123",
        )
        self.assertEqual(req.login, "student1")
        self.assertEqual(req.email, "student1@example.com")
        self.assertEqual(req.new_password, "newsecret123")

    def test_invalid_email_format(self):
        with self.assertRaises(ValidationError):
            PasswordResetRequest(
                login="student1",
                email="not-an-email",
                new_password="newsecret123",
            )

    def test_password_too_short(self):
        with self.assertRaises(ValidationError):
            PasswordResetRequest(
                login="student1",
                email="student1@example.com",
                new_password="1234567",
            )


class TestPasswordResetRepository(unittest.IsolatedAsyncioTestCase):
    async def test_reset_password_success(self):
        session = AsyncMock()
        repo = UserRepository(session)

        fake_user = SimpleNamespace(user_id=42, login="student1", email="student1@example.com")
        repo.get_user_by_login = AsyncMock(return_value=fake_user)

        fake_pwd_record = SimpleNamespace(user_id=42, password_hash="old_hash")
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = fake_pwd_record
        session.execute = AsyncMock(return_value=mock_result)

        result = await repo.reset_password(
            login="student1",
            email="STUDENT1@EXAMPLE.COM ",
            new_password="newpassword123",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.user_id, 42)
        self.assertNotEqual(fake_pwd_record.password_hash, "old_hash")
        session.commit.assert_awaited_once()

    async def test_reset_password_user_not_found(self):
        session = AsyncMock()
        repo = UserRepository(session)
        repo.get_user_by_login = AsyncMock(return_value=None)

        result = await repo.reset_password(
            login="unknown",
            email="unknown@example.com",
            new_password="newpassword123",
        )

        self.assertIsNone(result)
        session.commit.assert_not_awaited()

    async def test_reset_password_email_mismatch(self):
        session = AsyncMock()
        repo = UserRepository(session)
        fake_user = SimpleNamespace(user_id=42, login="student1", email="student1@example.com")
        repo.get_user_by_login = AsyncMock(return_value=fake_user)

        result = await repo.reset_password(
            login="student1",
            email="different@example.com",
            new_password="newpassword123",
        )

        self.assertIsNone(result)
        session.commit.assert_not_awaited()


class TestPasswordResetAPI(unittest.IsolatedAsyncioTestCase):
    @patch("src.api.auth.log_user_event", new_callable=AsyncMock)
    async def test_api_reset_password_success(self, mock_log_event):
        mock_user_repo = AsyncMock()
        fake_user = SimpleNamespace(user_id=42, login="student1", email="student1@example.com")
        mock_user_repo.reset_password.return_value = fake_user
        mock_db = AsyncMock()

        payload = PasswordResetRequest(
            login="student1",
            email="student1@example.com",
            new_password="newpassword123",
        )

        response = await reset_password(
            data=payload,
            user_repo=mock_user_repo,
            db=mock_db,
        )

        self.assertEqual(response, {"message": "Пароль успешно обновлен"})
        mock_log_event.assert_awaited_once_with(
            session=mock_db,
            user_id=42,
            event_type="password_reset",
        )

    async def test_api_reset_password_not_found_raises_400(self):
        mock_user_repo = AsyncMock()
        mock_user_repo.reset_password.return_value = None
        mock_db = AsyncMock()

        payload = PasswordResetRequest(
            login="student1",
            email="wrong@example.com",
            new_password="newpassword123",
        )

        with self.assertRaises(HTTPException) as ctx:
            await reset_password(
                data=payload,
                user_repo=mock_user_repo,
                db=mock_db,
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(
            ctx.exception.detail,
            "Пользователь с указанным логином и почтой не найден",
        )
