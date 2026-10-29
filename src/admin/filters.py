import datetime
from typing import Any
from sqlalchemy import Select
from starlette.requests import Request

from src.models.user import User
from src.models.user_event import UserEvent


class EventTimestampFilter:
    """
    Custom filter for telemetry events by timestamp.
    Supports quick presets (today, 24h, 7d, 30d) and custom date/time ranges (from - to).
    """
    has_operator = False
    template = "admin/filters/timestamp_filter.html"

    def __init__(self, title: str = "Период времени", parameter_name: str = "ts_range"):
        self.title = title
        self.parameter_name = parameter_name

    async def lookups(self, request: Request, model: Any, run_query: Any) -> list[tuple[str, str]]:
        return []

    async def get_filtered_query(self, query: Select, value: Any, model: Any) -> Select:
        if not value or value in ("", "__all"):
            return query

        clean_val = str(value).strip()
        now = datetime.datetime.now(datetime.timezone.utc)

        if clean_val == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return query.filter(UserEvent.timestamp >= start_of_day)

        if clean_val == "24h":
            start_time = now - datetime.timedelta(hours=24)
            return query.filter(UserEvent.timestamp >= start_time)

        if clean_val == "7d":
            start_time = now - datetime.timedelta(days=7)
            return query.filter(UserEvent.timestamp >= start_time)

        if clean_val == "30d":
            start_time = now - datetime.timedelta(days=30)
            return query.filter(UserEvent.timestamp >= start_time)

        # Custom date range: format is 'from_val__to_val' or single date
        if "__" in clean_val:
            parts = clean_val.split("__", 1)
            from_part = parts[0].strip()
            to_part = parts[1].strip() if len(parts) > 1 else ""

            if from_part:
                try:
                    dt_from = datetime.datetime.fromisoformat(from_part)
                    if dt_from.tzinfo is None:
                        dt_from = dt_from.replace(tzinfo=datetime.timezone.utc)
                    query = query.filter(UserEvent.timestamp >= dt_from)
                except (ValueError, TypeError):
                    pass

            if to_part:
                try:
                    dt_to = datetime.datetime.fromisoformat(to_part)
                    # If date only (length <= 10, e.g. YYYY-MM-DD), set to end of that day
                    if len(to_part) <= 10:
                        dt_to = dt_to.replace(hour=23, minute=59, second=59, microsecond=999999)
                    if dt_to.tzinfo is None:
                        dt_to = dt_to.replace(tzinfo=datetime.timezone.utc)
                    query = query.filter(UserEvent.timestamp <= dt_to)
                except (ValueError, TypeError):
                    pass

            return query

        # Single date provided
        try:
            dt = datetime.datetime.fromisoformat(clean_val)
            if len(clean_val) <= 10:
                dt_start = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
                dt_end = dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=datetime.timezone.utc)
                return query.filter(UserEvent.timestamp >= dt_start, UserEvent.timestamp <= dt_end)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return query.filter(UserEvent.timestamp >= dt)
        except (ValueError, TypeError):
            return query


class UserNicknameFilter:
    """
    Custom filter for telemetry events by user nickname (login).
    Uses case-insensitive ILIKE search on User.login without interfering with main table queries.
    """
    has_operator = False
    template = "admin/filters/user_nickname_filter.html"

    def __init__(self, title: str = "Ник пользователя", parameter_name: str = "user_nickname"):
        self.title = title
        self.parameter_name = parameter_name

    async def lookups(self, request: Request, model: Any, run_query: Any) -> list[tuple[str, str]]:
        return []

    async def get_filtered_query(self, query: Select, value: Any, model: Any) -> Select:
        if not value or value in ("", "__all"):
            return query

        clean_val = str(value).strip()
        if not clean_val:
            return query

        return query.filter(UserEvent.user.has(User.login.ilike(f"%{clean_val}%")))
