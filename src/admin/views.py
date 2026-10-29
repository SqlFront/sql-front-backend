from sqladmin import ModelView
from sqladmin.filters import AllUniqueStringValuesFilter

from src.admin.filters import EventTimestampFilter, UserNicknameFilter
from src.models.achievement import Achievement
from src.models.task import Task
from src.models.user import User
from src.models.user_event import UserEvent


class UserView(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [
        User.user_id,
        User.login,
        User.email,
        User.fullname,
        User.group,
        User.total_score,
    ]
    column_searchable_list = [
        User.login,
        User.email,
        User.fullname,
        User.group,
    ]
    column_sortable_list = [
        User.user_id,
        User.login,
        User.email,
        User.group,
        User.total_score,
    ]
    column_default_sort = (User.user_id, False)


class TaskView(ModelView, model=Task):
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-list-check"

    column_list = [
        Task.task_id,
        Task.mission_id,
        Task.title,
        Task.description,
        Task.clue,
        Task.expected_result,
        Task.tags,
    ]
    form_columns = [
        Task.mission_id,
        Task.task_id,
        Task.title,
        Task.description,
        Task.clue,
        Task.correct_query,
        Task.expected_result,
        Task.tags,
    ]
    column_searchable_list = [
        Task.task_id,
        Task.mission_id,
        Task.title,
    ]
    column_sortable_list = [
        Task.task_global_id,
        Task.task_id,
        Task.mission_id,
        Task.title,
    ]
    column_default_sort = (Task.task_global_id, False)
    can_create = True
    can_edit = True
    can_delete = True


class AchievementView(ModelView, model=Achievement):
    name = "Достижение"
    name_plural = "Достижения"
    icon = "fa-solid fa-trophy"

    column_list = [
        Achievement.achievement_id,
        Achievement.category_name,
        Achievement.icon,
        Achievement.name,
        Achievement.description,
        Achievement.historical_info,
        Achievement.tag,
        Achievement.required_count,
    ]
    column_searchable_list = [
        Achievement.achievement_id,
        Achievement.category_name,
        Achievement.name,
    ]
    column_sortable_list = [
        Achievement.achievement_id,
        Achievement.category_name,
        Achievement.name,
        Achievement.required_count,
    ]
    column_default_sort = (Achievement.achievement_id, False)


class UserEventView(ModelView, model=UserEvent):
    name = "Событие телеметрии"
    name_plural = "События телеметрии"
    icon = "fa-solid fa-chart-line"

    column_list = [
        UserEvent.id,
        UserEvent.timestamp,
        UserEvent.user_id,
        UserEvent.task_id,
        UserEvent.event_type,
        UserEvent.payload,
    ]
    column_labels = {
        UserEvent.id: "ID",
        UserEvent.timestamp: "Время (UTC)",
        UserEvent.user_id: "Пользователь (ник)",
        UserEvent.task_id: "ID задачи",
        UserEvent.event_type: "Тип события",
        UserEvent.payload: "Данные (JSON)",
    }
    column_formatters = {
        UserEvent.user_id: lambda m, a: f"{m.user.login} ({m.user.group})" if getattr(m, "user", None) and m.user and m.user.login else f"ID: {m.user_id}",
    }
    column_details_list = [
        UserEvent.id,
        UserEvent.timestamp,
        UserEvent.user_id,
        UserEvent.task_id,
        UserEvent.event_type,
        UserEvent.payload,
    ]
    column_searchable_list = [
        "user.login",
        "user.fullname",
        "user.email",
        UserEvent.event_type,
        UserEvent.user_id,
    ]
    search_placeholder = "Поиск по нику, ФИО, email, типу события, user_id..."

    column_filters = [
        EventTimestampFilter(title="Период времени"),
        UserNicknameFilter(title="Ник пользователя"),
        AllUniqueStringValuesFilter(UserEvent.event_type, title="Тип события"),
    ]

    column_sortable_list = [
        UserEvent.id,
        UserEvent.timestamp,
        UserEvent.user_id,
        UserEvent.task_id,
        UserEvent.event_type,
    ]
    column_default_sort = (UserEvent.timestamp, True)

    page_size = 25
    page_size_options = [10, 25, 50, 100]

    # Режим read-only для защиты аудита
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
