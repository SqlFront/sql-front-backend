from collections import Counter, defaultdict
from typing import Optional, Sequence, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request

from database import AsyncSessionLocal
from src.models.user_event import UserEvent


def build_analytics_figure(events: Sequence[UserEvent]) -> Tuple[bool, Optional[str]]:
    """
    Build interactive Plotly analytics dashboard from telemetry events.
    Returns (has_data, graph_html).
    """
    if not events:
        return False, None

    # 1. Activity by date
    date_counts = Counter()
    for ev in events:
        if ev.timestamp:
            date_str = ev.timestamp.strftime("%Y-%m-%d") if hasattr(ev.timestamp, "strftime") else str(ev.timestamp)[:10]
            date_counts[date_str] += 1

    sorted_dates = sorted(date_counts.keys())
    counts_by_date = [date_counts[d] for d in sorted_dates]

    # 2. Top difficult tasks by error occurrences
    task_errors = Counter()
    task_attempts = Counter()
    for ev in events:
        if ev.task_id is not None:
            task_attempts[ev.task_id] += 1
            event_type = (ev.event_type or "").lower()
            if "error" in event_type or "fail" in event_type:
                task_errors[ev.task_id] += 1

    top_task_ids = [tid for tid, _ in task_errors.most_common(10)]
    task_labels = [f"Задача #{tid}" for tid in top_task_ids]
    error_counts = [task_errors[tid] for tid in top_task_ids]

    # Create subplots
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "Динамика активности по дням",
            "Топ сложных задач (по количеству ошибок)",
        ),
    )

    fig.add_trace(
        go.Bar(
            x=sorted_dates,
            y=counts_by_date,
            name="События",
            marker_color="#206bc4",
        ),
        row=1,
        col=1,
    )

    if top_task_ids:
        fig.add_trace(
            go.Bar(
                x=task_labels,
                y=error_counts,
                name="Ошибки",
                marker_color="#d63939",
            ),
            row=1,
            col=2,
        )
    else:
        # Fallback if no task-specific errors
        fig.add_trace(
            go.Bar(
                x=["Нет ошибок"],
                y=[0],
                name="Ошибки",
                marker_color="#d63939",
            ),
            row=1,
            col=2,
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=30, r=30, t=50, b=40),
        height=450,
        showlegend=False,
    )

    graph_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    return True, graph_html


class AnalyticsDashboardView(BaseView):
    """
    Custom sqladmin view providing educational analytics and telemetry visualization.
    Accessible at /admin/analytics.
    """

    name = "Аналитика"
    icon = "fa-solid fa-chart-line"
    identity = "analytics"

    @expose("/analytics", methods=["GET"], identity="analytics")
    async def dashboard_page(self, request: Request):
        session_maker = getattr(self._admin_ref, "session_maker", None) or AsyncSessionLocal
        async with session_maker() as session:
            stmt = select(UserEvent).order_by(UserEvent.timestamp.desc()).limit(5000)
            result = await session.execute(stmt)
            events = result.scalars().all()

        has_data, graph_html = build_analytics_figure(events)

        return await self.templates.TemplateResponse(
            request,
            "admin/analytics.html",
            {
                "request": request,
                "has_data": has_data,
                "graph_html": graph_html,
            },
        )
