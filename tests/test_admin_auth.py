import pytest
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.admin.auth import AdminAuth
from config import settings


def create_mock_request(session=None, form_data=None):
    scope = {
        "type": "http",
        "session": session if session is not None else {},
        "headers": [],
    }

    async def receive():
        return {"type": "http.request"}

    request = Request(scope, receive)
    if form_data is not None:
        async def form():
            return FormData(form_data)
        request.form = form
    return request


@pytest.mark.anyio
async def test_admin_auth_login_success():
    auth = AdminAuth(secret_key=settings.SECRET_KEY)
    session = {}
    request = create_mock_request(
        session=session,
        form_data={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )

    result = await auth.login(request)
    assert result is True
    assert session.get("token") == "admin-token"
    assert session.get("user_id") == settings.ADMIN_USERNAME


@pytest.mark.anyio
async def test_admin_auth_login_failure():
    auth = AdminAuth(secret_key=settings.SECRET_KEY)
    session = {}
    request = create_mock_request(
        session=session,
        form_data={"username": "wrong", "password": "bad"},
    )

    result = await auth.login(request)
    assert result is False
    assert "token" not in session


@pytest.mark.anyio
async def test_admin_auth_authenticate_valid():
    auth = AdminAuth(secret_key=settings.SECRET_KEY)
    session = {"token": "admin-token", "user_id": settings.ADMIN_USERNAME}
    request = create_mock_request(session=session)

    result = await auth.authenticate(request)
    assert result is True


@pytest.mark.anyio
async def test_admin_auth_authenticate_invalid():
    auth = AdminAuth(secret_key=settings.SECRET_KEY)
    request_empty = create_mock_request(session={})
    assert await auth.authenticate(request_empty) is False

    request_invalid = create_mock_request(session={"token": "invalid"})
    assert await auth.authenticate(request_invalid) is False


@pytest.mark.anyio
async def test_admin_auth_logout():
    auth = AdminAuth(secret_key=settings.SECRET_KEY)
    session = {"token": "admin-token", "user_id": settings.ADMIN_USERNAME}
    request = create_mock_request(session=session)

    result = await auth.logout(request)
    assert result is True
    assert len(session) == 0
