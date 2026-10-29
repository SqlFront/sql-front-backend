"""
Admin module for SQL-Front platform.
"""
import os
from fastapi import FastAPI
from sqladmin import Admin

from database import engine as default_engine
from src.admin.auth import AdminAuth
from src.admin.dashboard import AnalyticsDashboardView
from src.admin.views import AchievementView, TaskView, UserEventView, UserView

__all__ = [
    "setup_admin",
    "AdminAuth",
    "UserView",
    "TaskView",
    "AchievementView",
    "UserEventView",
    "AnalyticsDashboardView",
]

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "templates",
)


def setup_admin(app: FastAPI, engine=None, authentication_backend=None) -> Admin:
    """
    Initialize and mount SQLAdmin on FastAPI app.
    Registers ModelViews (User, Task, Achievement, UserEvent)
    and AnalyticsDashboardView.
    """
    auth = authentication_backend or AdminAuth()
    admin = Admin(
        app,
        engine or default_engine,
        authentication_backend=auth,
        base_url="/admin",
        title="SQL-Front Admin",
        templates_dir=TEMPLATES_DIR,
    )

    admin.add_view(UserView)
    admin.add_view(TaskView)
    admin.add_view(AchievementView)
    admin.add_view(UserEventView)
    admin.add_view(AnalyticsDashboardView)

    return admin
