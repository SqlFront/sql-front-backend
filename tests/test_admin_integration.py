import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings
from src.admin import setup_admin


@pytest.mark.anyio
async def test_admin_integration_mounting_and_auth():
    app = FastAPI()
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    admin = setup_admin(app, engine=test_engine)

    assert admin is not None
    assert admin.app == app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        # 1. Unauthenticated request to /admin/ should redirect to /admin/login
        response = await client.get("/admin/")
        assert response.status_code in [302, 303, 307]
        assert "/admin/login" in response.headers.get("location", "")

        # 2. Login page should be accessible
        login_page_response = await client.get("/admin/login")
        assert login_page_response.status_code == 200
        assert "username" in login_page_response.text.lower()

        # 3. Invalid credentials should fail
        bad_login_response = await client.post(
            "/admin/login",
            data={"username": "wrong_user", "password": "wrong_password"}
        )
        assert bad_login_response.status_code in [200, 400]

        # 4. Valid credentials should succeed and return session cookie
        login_response = await client.post(
            "/admin/login",
            data={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD}
        )
        assert login_response.status_code in [302, 303]
        session_cookie = client.cookies.get("session") or client.cookies.get("admin_session")
        assert session_cookie is not None or len(client.cookies) > 0

        # 5. Accessing /admin with authenticated client
        admin_response = await client.get("/admin", follow_redirects=True)
        assert admin_response.status_code == 200

        # 6. Accessing /admin/analytics with authenticated client
        analytics_response = await client.get("/admin/analytics")
        assert analytics_response.status_code == 200
        assert "Аналитика" in analytics_response.text or "телеметрия" in analytics_response.text
