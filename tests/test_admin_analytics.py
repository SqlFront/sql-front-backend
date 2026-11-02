import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings
from src.models.user import User
from src.models.user_event import UserEvent
from src.admin import setup_admin
from src.admin.views import UserEventView


def test_user_event_view_search_placeholder_method():
    """Ensure search_placeholder is a callable method returning expected string."""
    view = UserEventView()
    assert callable(view.search_placeholder)
    assert view.search_placeholder() == "Поиск по нику, ФИО, email, типу события, user_id..."


@pytest.mark.anyio
async def test_admin_user_event_list_authenticated_200():
    """
    Ensure GET /admin/user-event/list returns HTTP 200 without 'str object is not callable' error
    when accessed by an authenticated administrator.
    """
    app = FastAPI()
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with test_engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(UserEvent.__table__.create)

    setup_admin(app, engine=test_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as admin
        login_response = await client.post(
            "/admin/login",
            data={
                "username": settings.ADMIN_USERNAME,
                "password": settings.ADMIN_PASSWORD,
            },
        )
        assert login_response.status_code in [302, 303]

        # 2. Access /admin/user-event/list
        response = await client.get("/admin/user-event/list")
        assert response.status_code == 200
        assert "События телеметрии" in response.text
        assert "Поиск по нику, ФИО, email, типу события, user_id..." in response.text
