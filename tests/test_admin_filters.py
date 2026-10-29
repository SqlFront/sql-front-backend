import datetime
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.user import User
from src.models.user_event import UserEvent
from src.admin.filters import EventTimestampFilter, UserNicknameFilter
from src.admin.views import UserEventView


@pytest.mark.anyio
async def test_event_timestamp_filter_presets():
    ts_filter = EventTimestampFilter()
    now = datetime.datetime.now(datetime.timezone.utc)

    # Empty / None should not filter
    q_base = select(UserEvent)
    q_empty = await ts_filter.get_filtered_query(q_base, "", UserEvent)
    assert str(q_empty) == str(q_base)

    # Preset today
    q_today = await ts_filter.get_filtered_query(q_base, "today", UserEvent)
    assert "timestamp >=" in str(q_today)

    # Preset 24h
    q_24h = await ts_filter.get_filtered_query(q_base, "24h", UserEvent)
    assert "timestamp >=" in str(q_24h)

    # Preset 7d
    q_7d = await ts_filter.get_filtered_query(q_base, "7d", UserEvent)
    assert "timestamp >=" in str(q_7d)

    # Preset 30d
    q_30d = await ts_filter.get_filtered_query(q_base, "30d", UserEvent)
    assert "timestamp >=" in str(q_30d)


@pytest.mark.anyio
async def test_event_timestamp_filter_custom_range():
    ts_filter = EventTimestampFilter()
    q_base = select(UserEvent)

    # Custom range with start and end
    q_range = await ts_filter.get_filtered_query(q_base, "2026-10-01__2026-10-15", UserEvent)
    sql_str = str(q_range)
    assert "timestamp >=" in sql_str
    assert "timestamp <=" in sql_str

    # Only start
    q_start = await ts_filter.get_filtered_query(q_base, "2026-10-01__", UserEvent)
    assert "timestamp >=" in str(q_start)

    # Only end
    q_end = await ts_filter.get_filtered_query(q_base, "__2026-10-15", UserEvent)
    assert "timestamp <=" in str(q_end)


@pytest.mark.anyio
async def test_user_nickname_filter():
    nick_filter = UserNicknameFilter()
    q_base = select(UserEvent)

    # Empty value
    q_empty = await nick_filter.get_filtered_query(q_base, "", UserEvent)
    assert str(q_empty) == str(q_base)

    # Nickname filter
    q_nick = await nick_filter.get_filtered_query(q_base, "student_test", UserEvent)
    sql_str = str(q_nick)
    assert "EXISTS" in sql_str
    assert "users" in sql_str
    assert "login" in sql_str


def test_user_event_view_custom_filters_registered():
    filters = UserEventView().get_filters()
    assert len(filters) >= 2
    param_names = [f.parameter_name for f in filters]
    assert "ts_range" in param_names
    assert "user_nickname" in param_names
    assert "event_type" in param_names

    # Formatter test
    mock_event = UserEvent(id=1, user_id=42, event_type="task_submitted")
    mock_user = User(user_id=42, login="test_user", group="БСБО-01-21")
    mock_event.user = mock_user

    formatter = UserEventView.column_formatters[UserEvent.user_id]
    result = formatter(mock_event, "user_id")
    assert "test_user" in result
    assert "БСБО-01-21" in result
