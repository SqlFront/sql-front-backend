import datetime
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqladmin import Admin, BaseView
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database import Base
from src.models.user_event import UserEvent
from src.admin.dashboard import AnalyticsDashboardView, build_analytics_figure


@pytest.mark.anyio
async def test_analytics_dashboard_view_definition():
    assert issubclass(AnalyticsDashboardView, BaseView)
    assert AnalyticsDashboardView.identity == "analytics"
    assert AnalyticsDashboardView.name == "Аналитика"


@pytest.mark.anyio
async def test_build_analytics_figure_empty():
    has_data, graph_html = build_analytics_figure([])
    assert has_data is False
    assert graph_html is None


@pytest.mark.anyio
async def test_build_analytics_figure_with_data():
    sample_events = [
        UserEvent(
            id=1,
            timestamp=datetime.datetime(2026, 10, 14, 10, 0, 0),
            user_id=1,
            task_id=5,
            event_type="task_submit_error",
            payload={"error": "Syntax error"}
        ),
        UserEvent(
            id=2,
            timestamp=datetime.datetime(2026, 10, 14, 11, 0, 0),
            user_id=1,
            task_id=5,
            event_type="task_submit_success",
            payload={"score": 100}
        ),
    ]
    has_data, graph_html = build_analytics_figure(sample_events)
    assert has_data is True
    assert graph_html is not None
    assert "plotly" in graph_html.lower()


@pytest.mark.anyio
async def test_analytics_dashboard_http_endpoint():
    # Setup in-memory SQLite database
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(UserEvent.__table__.create)

    test_session_maker = sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    app = FastAPI()
    admin = Admin(
        app,
        test_engine,
        session_maker=test_session_maker,
        base_url="/admin",
        templates_dir="templates",
    )
    admin.add_view(AnalyticsDashboardView)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/admin/analytics")
        assert response.status_code == 200
        # Empty DB: should display "Нет данных для отображения"
        assert "Нет данных для отображения" in response.text

        # Now add some events
        async with test_session_maker() as session:
            ev = UserEvent(
                id=1,
                timestamp=datetime.datetime.now(),
                user_id=10,
                task_id=2,
                event_type="task_error",
                payload={"msg": "err"}
            )
            session.add(ev)
            await session.commit()

        # Query again
        response_with_data = await client.get("/admin/analytics")
        assert response_with_data.status_code == 200
        assert "plotly" in response_with_data.text.lower()
