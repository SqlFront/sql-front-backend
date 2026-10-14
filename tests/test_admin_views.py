import pytest
from sqladmin import ModelView

from src.models import User, Task, Achievement, UserEvent
from src.admin.views import UserView, TaskView, AchievementView, UserEventView


def test_user_view_configuration():
    assert issubclass(UserView, ModelView)
    assert UserView.model == User
    assert User.login in UserView.column_list or "login" in [getattr(c, "key", str(c)) for c in UserView.column_list]
    assert User.email in UserView.column_list or "email" in [getattr(c, "key", str(c)) for c in UserView.column_list]
    assert User.group in UserView.column_list or "group" in [getattr(c, "key", str(c)) for c in UserView.column_list]


def test_task_view_configuration():
    assert issubclass(TaskView, ModelView)
    assert TaskView.model == Task
    assert Task.title in TaskView.column_list or "title" in [getattr(c, "key", str(c)) for c in TaskView.column_list]


def test_achievement_view_configuration():
    assert issubclass(AchievementView, ModelView)
    assert AchievementView.model == Achievement
    assert Achievement.name in AchievementView.column_list or "name" in [getattr(c, "key", str(c)) for c in AchievementView.column_list]


def test_user_event_view_read_only():
    assert issubclass(UserEventView, ModelView)
    assert UserEventView.model == UserEvent
    assert UserEventView.can_create is False
    assert UserEventView.can_edit is False
    assert UserEventView.can_delete is False
    assert UserEvent.event_type in UserEventView.column_list or "event_type" in [getattr(c, "key", str(c)) for c in UserEventView.column_list]
