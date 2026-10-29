import datetime
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request

from database import AsyncSessionLocal
from src.models.task import Task
from src.models.user import User
from src.models.user_event import UserEvent


def build_analytics_dashboard_data(
    events: Sequence[UserEvent],
    users: Optional[Sequence[User]] = None,
    tasks: Optional[Sequence[Task]] = None,
) -> Dict[str, Any]:
    """
    Compute pedagogical analytics metrics and generate interactive Plotly visualizations
    for instructors: velocity, AI/cheating heuristics, difficulty hotspots, and cohorts.
    """
    if not events:
        return {
            "has_data": False,
            "kpis": {
                "total_students": 0,
                "total_submissions": 0,
                "success_rate": 0.0,
                "avg_solve_time_min": 0.0,
                "ai_suspicions_count": 0,
            },
            "charts": {},
            "ai_suspicious_solutions": [],
        }

    user_map = {u.user_id: u for u in (users or [])}
    task_map = {t.task_global_id: t for t in (tasks or [])}

    # ---------------------------------------------------------
    # 1. Base aggregations and tracking
    # ---------------------------------------------------------
    dates_counter = Counter()
    hours_counter = Counter()
    total_submissions = 0
    successful_submissions = 0
    task_submissions = Counter()
    task_failures = Counter()
    clue_purchases = defaultdict(lambda: Counter())  # task_id -> {clue_type: count}

    # Group events by (user_id, task_id) to reconstruct student journey per task
    user_task_events = defaultdict(list)
    active_users = set()

    for ev in events:
        ts = ev.timestamp
        if ts:
            date_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
            dates_counter[date_str] += 1
            hour_int = ts.hour if hasattr(ts, "hour") else 0
            hours_counter[hour_int] += 1

        uid = ev.user_id
        if uid:
            active_users.add(uid)

        tid = ev.task_id
        etype = (ev.event_type or "").lower()
        payload = ev.payload or {}

        if uid and tid is not None:
            user_task_events[(uid, tid)].append(ev)

        if "submitted" in etype or etype == "task_submitted":
            total_submissions += 1
            is_correct = bool(payload.get("is_correct", False))
            if is_correct:
                successful_submissions += 1
            else:
                task_failures[tid] += 1
            task_submissions[tid] += 1

        elif "error" in etype or "fail" in etype:
            total_submissions += 1
            task_failures[tid] += 1
            task_submissions[tid] += 1

        elif etype == "purchase_clue":
            clue_type = payload.get("clue_type", 1)
            clue_purchases[tid][clue_type] += 1

    # ---------------------------------------------------------
    # 2. Time & Velocity per task & Mission metrics
    # ---------------------------------------------------------
    task_durations = []  # list of durations in seconds
    mission_user_times = defaultdict(lambda: defaultdict(list))  # mission_id -> user_id -> [timestamps]
    ai_candidates = []

    for (uid, tid), ev_list in user_task_events.items():
        ev_list.sort(key=lambda x: x.timestamp or datetime.datetime.min)

        start_time = None
        first_success_time = None
        attempts_before_success = 0
        inactivities_count = 0
        clues_count = 0
        mission_id = None

        task_obj = task_map.get(tid)
        if task_obj:
            mission_id = task_obj.mission_id

        for ev in ev_list:
            etype = (ev.event_type or "").lower()
            p = ev.payload or {}
            if mission_id is None and "mission_id" in p:
                mission_id = p["mission_id"]

            if etype in ("task_started", "task_attempt") and start_time is None:
                start_time = ev.timestamp

            if etype == "user_inactive":
                inactivities_count += 1

            if etype == "purchase_clue":
                clues_count += 1

            if etype in ("task_submitted", "task_submit_success"):
                is_ok = bool(p.get("is_correct", False)) or etype == "task_submit_success"
                if is_ok:
                    if first_success_time is None:
                        first_success_time = ev.timestamp
                else:
                    attempts_before_success += 1
            elif "error" in etype or "fail" in etype:
                attempts_before_success += 1

        if start_time and first_success_time and first_success_time >= start_time:
            dur = (first_success_time - start_time).total_seconds()
            if 0 < dur < 86400:  # exclude unrealistic outliers (> 24 hours)
                task_durations.append(dur)

                # Track mission timestamps
                if mission_id is not None:
                    mission_user_times[mission_id][uid].extend([start_time, first_success_time])

                # AI / Fast-solution anomaly heuristic:
                # 1) Solved under 30s on attempt 0-1 without clues (direct copy-paste / solution leak), OR
                # 2) Solved under 60s on attempt 0-1 with tab switching (user_inactive >= 1) without clues
                is_suspicious = (attempts_before_success <= 1) and (clues_count == 0) and (
                    (dur < 30) or (dur < 60 and inactivities_count >= 1)
                )
                u = user_map.get(uid)
                login_label = u.login if u else f"User #{uid}"
                group_label = getattr(u, "group", None) or "—"
                task_num = getattr(task_obj, "task_id", getattr(task_obj, "task_number", tid))
                t_label = f"Миссия {task_obj.mission_id}.{task_num}: {task_obj.title}" if task_obj else f"Задача #{tid}"

                ai_candidates.append({
                    "user_id": uid,
                    "login": login_label,
                    "group": group_label,
                    "task_id": tid,
                    "task_label": t_label,
                    "duration_sec": round(dur, 1),
                    "attempts": attempts_before_success,
                    "inactivities": inactivities_count,
                    "timestamp": first_success_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(first_success_time, "strftime") else str(first_success_time),
                    "suspicious": is_suspicious,
                })

    # Sort AI candidates (suspicious first, then shortest duration)
    ai_candidates.sort(key=lambda x: (not x["suspicious"], x["duration_sec"]))
    suspicious_solutions = [c for c in ai_candidates if c["suspicious"]]

    # ---------------------------------------------------------
    # 3. Mission durations (Min / Avg / Max)
    # ---------------------------------------------------------
    mission_stats = {}
    for mid in sorted(mission_user_times.keys()):
        m_durations = []
        for uid, t_list in mission_user_times[mid].items():
            if t_list:
                m_dur = (max(t_list) - min(t_list)).total_seconds() / 60.0  # in minutes
                if 0.5 <= m_dur <= 720:  # 30 sec to 12 hours
                    m_durations.append(m_dur)
        if m_durations:
            mission_stats[mid] = {
                "min": round(min(m_durations), 1),
                "avg": round(sum(m_durations) / len(m_durations), 1),
                "max": round(max(m_durations), 1),
            }

    # ---------------------------------------------------------
    # 4. Cohort / Group Analytics
    # ---------------------------------------------------------
    group_stats = defaultdict(lambda: {"students": set(), "scores": [], "attempts": 0, "submissions": 0})
    for u in (users or []):
        grp = getattr(u, "group", None) or "Без группы"
        group_stats[grp]["students"].add(u.user_id)
        if getattr(u, "total_score", None) is not None:
            group_stats[grp]["scores"].append(u.total_score)

    for (uid, _), ev_list in user_task_events.items():
        u = user_map.get(uid)
        grp = getattr(u, "group", None) or "Без группы" if u else "Без группы"
        group_stats[grp]["submissions"] += len(ev_list)

    # ---------------------------------------------------------
    # 5. Build Interactive Plotly Charts
    # ---------------------------------------------------------

    # --- Chart 1: Time & Velocity (Mission box/bar + Task histogram) ---
    fig_time = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Время прохождения миссий (Мин / Среднее / Макс, мин)", "Распределение времени решения задач (мин)"),
    )

    if mission_stats:
        m_labels = [f"Миссия {m}" for m in mission_stats.keys()]
        m_mins = [mission_stats[m]["min"] for m in mission_stats.keys()]
        m_avgs = [mission_stats[m]["avg"] for m in mission_stats.keys()]
        m_maxs = [mission_stats[m]["max"] for m in mission_stats.keys()]

        fig_time.add_trace(go.Bar(x=m_labels, y=m_mins, name="Минимум", marker_color="#2fb344"), row=1, col=1)
        fig_time.add_trace(go.Bar(x=m_labels, y=m_avgs, name="Среднее", marker_color="#206bc4"), row=1, col=1)
        fig_time.add_trace(go.Bar(x=m_labels, y=m_maxs, name="Максимум", marker_color="#f59f00"), row=1, col=1)
    else:
        fig_time.add_trace(go.Bar(x=["Миссии 0-5"], y=[0], name="Нет данных"), row=1, col=1)

    if task_durations:
        durations_min = [d / 60.0 for d in task_durations if d <= 3600]
        fig_time.add_trace(go.Histogram(x=durations_min, nbinsx=25, marker_color="#4299e1", name="Задачи"), row=1, col=2)
    else:
        fig_time.add_trace(go.Histogram(x=[0], name="Задачи"), row=1, col=2)

    fig_time.update_layout(template="plotly_white", height=420, margin=dict(l=30, r=30, t=50, b=40))

    # --- Chart 2: AI Detection & Scatter Plot ---
    fig_ai = go.Figure()
    if ai_candidates:
        x_vals = [c["duration_sec"] for c in ai_candidates]
        y_vals = [c["attempts"] for c in ai_candidates]
        inactive_vals = [c["inactivities"] for c in ai_candidates]
        hover_texts = [
            f"Студент: {c['login']} ({c['group']})<br>{c['task_label']}<br>Время: {c['duration_sec']} с<br>Ошибок: {c['attempts']}<br>Смена вкладок: {c['inactivities']}"
            for c in ai_candidates
        ]

        fig_ai.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                marker=dict(
                    size=12,
                    color=inactive_vals,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Смена вкладок"),
                ),
                text=hover_texts,
                hoverinfo="text",
                name="Решения",
            )
        )

        # Highlight Anomaly / AI suspicion zone (< 45s, 0-1 attempts)
        max_y = max(y_vals) if y_vals else 5
        fig_ai.add_shape(
            type="rect",
            x0=0, x1=45,
            y0=-0.5, y1=1.5,
            line=dict(color="#d63939", width=2, dash="dash"),
            fillcolor="rgba(214, 57, 57, 0.15)",
        )
        fig_ai.add_annotation(
            x=22.5, y=1.2,
            text="Зона подозрения на ИИ / копипасту (< 45 сек, без ошибок)",
            showarrow=False,
            font=dict(color="#d63939", size=11, family="Arial"),
        )
    else:
        fig_ai.add_trace(go.Scatter(x=[0], y=[0], mode="markers", name="Нет данных"))

    fig_ai.update_layout(
        title="Корреляция: Скорость решения vs Число ошибок (цвет = уход со страницы)",
        xaxis_title="Время решения задачи (секунды)",
        yaxis_title="Число ошибочных попыток до сдачи",
        template="plotly_white",
        height=450,
        margin=dict(l=30, r=30, t=50, b=40),
    )

    # --- Chart 3: Difficulty & Clues (Failure Rate + Hints) ---
    fig_diff = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Топ задач по проценту ошибок (Failure Rate, %)", "Востребованность подсказок 1 и 2 уровня"),
    )

    task_rates = []
    for tid, tot in task_submissions.items():
        if tot >= 1:
            fails = task_failures[tid]
            rate = round((fails / tot) * 100.0, 1)
            t_obj = task_map.get(tid)
            t_num = getattr(t_obj, "task_id", getattr(t_obj, "task_number", tid))
            lbl = f"{t_obj.mission_id}.{t_num}" if t_obj else f"#{tid}"
            task_rates.append((lbl, rate, tot))

    task_rates.sort(key=lambda x: x[1], reverse=True)
    top_diff = task_rates[:12]

    if top_diff:
        fig_diff.add_trace(
            go.Bar(
                x=[t[0] for t in top_diff],
                y=[t[1] for t in top_diff],
                marker_color="#d63939",
                name="Failure %",
            ),
            row=1, col=1
        )
    else:
        fig_diff.add_trace(go.Bar(x=["Нет данных"], y=[0]), row=1, col=1)

    top_clue_tids = sorted(clue_purchases.keys(), key=lambda t: sum(clue_purchases[t].values()), reverse=True)[:10]
    if top_clue_tids:
        clue_labels = [f"#{tid}" for tid in top_clue_tids]
        clue1 = [clue_purchases[tid][1] for tid in top_clue_tids]
        clue2 = [clue_purchases[tid][2] for tid in top_clue_tids]
        fig_diff.add_trace(go.Bar(x=clue_labels, y=clue1, name="Подсказка 1", marker_color="#f59f00"), row=1, col=2)
        fig_diff.add_trace(go.Bar(x=clue_labels, y=clue2, name="Подсказка 2", marker_color="#ae3ec9"), row=1, col=2)
    else:
        fig_diff.add_trace(go.Bar(x=["Нет данных"], y=[0]), row=1, col=2)

    fig_diff.update_layout(template="plotly_white", height=420, margin=dict(l=30, r=30, t=50, b=40))

    # --- Chart 4: Academic Cohorts / Groups ---
    fig_groups = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Средний балл по учебным группам", "Активность сабмитов по группам"),
    )

    group_names = [g for g in sorted(group_stats.keys()) if g != "Без группы"]
    if not group_names and "Без группы" in group_stats:
        group_names = ["Без группы"]

    if group_names:
        avg_scores = [
            round(sum(group_stats[g]["scores"]) / len(group_stats[g]["scores"]), 1)
            if group_stats[g]["scores"] else 0
            for g in group_names
        ]
        sub_counts = [group_stats[g]["submissions"] for g in group_names]

        fig_groups.add_trace(go.Bar(x=group_names, y=avg_scores, marker_color="#206bc4", name="Средний балл"), row=1, col=1)
        fig_groups.add_trace(go.Bar(x=group_names, y=sub_counts, marker_color="#0ca678", name="Сабмиты"), row=1, col=2)
    else:
        fig_groups.add_trace(go.Bar(x=["Группы"], y=[0]), row=1, col=1)
        fig_groups.add_trace(go.Bar(x=["Группы"], y=[0]), row=1, col=2)

    fig_groups.update_layout(template="plotly_white", height=420, margin=dict(l=30, r=30, t=50, b=40))

    # --- Chart 5: Overview (Daily dynamics + Hour heatmap) ---
    fig_overview = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Динамика активности по дням", "Почасовая активность (00:00 - 23:00)"),
    )
    sorted_dates = sorted(dates_counter.keys())
    counts_by_date = [dates_counter[d] for d in sorted_dates]
    fig_overview.add_trace(go.Bar(x=sorted_dates, y=counts_by_date, marker_color="#206bc4", name="События"), row=1, col=1)

    hours_x = [f"{h:02d}:00" for h in range(24)]
    hours_y = [hours_counter[h] for h in range(24)]
    fig_overview.add_trace(go.Bar(x=hours_x, y=hours_y, marker_color="#4263eb", name="Часы"), row=1, col=2)
    fig_overview.update_layout(template="plotly_white", height=420, margin=dict(l=30, r=30, t=50, b=40), showlegend=False)

    # ---------------------------------------------------------
    # Render all figures to HTML
    # ---------------------------------------------------------
    charts_html = {
        "overview": fig_overview.to_html(full_html=False, include_plotlyjs=False),
        "time_velocity": fig_time.to_html(full_html=False, include_plotlyjs=False),
        "ai_integrity": fig_ai.to_html(full_html=False, include_plotlyjs=False),
        "difficulty": fig_diff.to_html(full_html=False, include_plotlyjs=False),
        "groups": fig_groups.to_html(full_html=False, include_plotlyjs=False),
    }

    # KPIs
    total_students = len(users) if users else len(active_users)
    success_rate = round((successful_submissions / total_submissions) * 100.0, 1) if total_submissions > 0 else 0.0
    avg_solve_time_min = round((sum(task_durations) / len(task_durations)) / 60.0, 1) if task_durations else 0.0

    return {
        "has_data": True,
        "kpis": {
            "total_students": total_students,
            "total_submissions": total_submissions,
            "success_rate": success_rate,
            "avg_solve_time_min": avg_solve_time_min,
            "ai_suspicions_count": len(suspicious_solutions),
        },
        "charts": charts_html,
        "ai_suspicious_solutions": suspicious_solutions[:15],
    }


def build_analytics_figure(events: Sequence[UserEvent]) -> Tuple[bool, Optional[str]]:
    """
    Backward-compatible wrapper returning overview graph HTML.
    """
    data = build_analytics_dashboard_data(events)
    if not data["has_data"]:
        return False, None
    return True, data["charts"].get("overview")


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
        events: List[UserEvent] = []
        users: List[User] = []
        tasks: List[Task] = []

        try:
            async with session_maker() as session:
                stmt_ev = select(UserEvent).order_by(UserEvent.timestamp.desc()).limit(10000)
                events = (await session.execute(stmt_ev)).scalars().all()

                try:
                    stmt_u = select(User)
                    users = (await session.execute(stmt_u)).scalars().all()
                except Exception:
                    users = []

                try:
                    stmt_t = select(Task)
                    tasks = (await session.execute(stmt_t)).scalars().all()
                except Exception:
                    tasks = []
        except Exception:
            events = []

        dashboard_data = build_analytics_dashboard_data(events, users=users, tasks=tasks)

        return await self.templates.TemplateResponse(
            request,
            "admin/analytics.html",
            {
                "request": request,
                "has_data": dashboard_data["has_data"],
                "kpis": dashboard_data["kpis"],
                "charts": dashboard_data["charts"],
                "ai_suspicious_solutions": dashboard_data["ai_suspicious_solutions"],
                # Backward compatibility
                "graph_html": dashboard_data["charts"].get("overview"),
            },
        )
