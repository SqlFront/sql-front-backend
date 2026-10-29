import datetime
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqladmin import Admin, BaseView
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database import Base
from src.models.user_event import UserEvent
from src.models.user import User
from src.models.task import Task
from src.admin import TEMPLATES_DIR
from src.admin.dashboard import (
    AnalyticsDashboardView,
    build_analytics_figure,
    build_analytics_dashboard_data,
)


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
async def test_build_analytics_dashboard_data_ai_detection():
    # User 1 starts task 10, goes inactive, submits 20 seconds later on attempt 1
    t0 = datetime.datetime(2026, 10, 14, 12, 0, 0)
    t1 = t0 + datetime.timedelta(seconds=5)
    t2 = t0 + datetime.timedelta(seconds=20)

    events = [
        UserEvent(id=1, timestamp=t0, user_id=101, task_id=10, event_type="task_started", payload={"mission_id": 1, "task_id": 1}),
        UserEvent(id=2, timestamp=t1, user_id=101, task_id=10, event_type="user_inactive", payload={}),
        UserEvent(id=3, timestamp=t2, user_id=101, task_id=10, event_type="task_submitted", payload={"is_correct": True}),
    ]

    user = User(user_id=101, login="student_fast", fullname="Test Student", group="IKBO-01-24", total_score=500)
    task = Task(task_global_id=10, mission_id=1, task_id=1, title="Select Query")

    data = build_analytics_dashboard_data(events, users=[user], tasks=[task])

    assert data["has_data"] is True
    assert data["kpis"]["total_students"] == 1
    assert data["kpis"]["ai_suspicions_count"] == 1
    assert len(data["ai_suspicious_solutions"]) == 1
    assert data["ai_suspicious_solutions"][0]["login"] == "student_fast"
    assert data["ai_suspicious_solutions"][0]["duration_sec"] == 20.0
    assert "ai_integrity" in data["charts"]
    assert "time_velocity" in data["charts"]
    assert "difficulty" in data["charts"]
    assert "groups" in data["charts"]


@pytest.mark.anyio
async def test_analytics_dashboard_http_endpoint():
    # Setup in-memory SQLite database
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
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
        templates_dir=TEMPLATES_DIR,
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
        assert "Детекция ИИ и аномалий" in response_with_data.text
        assert "Скорость и время миссий" in response_with_data.text
        assert "Учебные группы" in response_with_data.text
