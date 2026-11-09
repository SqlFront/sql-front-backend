from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    mission_id: int
    title: str
    description: str


class TaskCreate(TaskBase):
    clue: str
    correct_query: Optional[str] = None
    expected_result: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TaskInfo(TaskBase):
    task_global_id: int
    task_id: int
    title: str
    is_solved: bool
    user_solution: Optional[str] = None

    class Config:
        from_attributes = True


class MissionTasks(BaseModel):
    mission_id: int
    tasks: List[TaskInfo]


class GroupedTasksResponse(BaseModel):
    missions: Dict[int, MissionTasks]


class TaskClue(BaseModel):
    clue: str


class TaskExpectedResult(BaseModel):
    expected_result: Dict[str, Any]


class TasksCount(BaseModel):
    easy_tasks_total: int
    medium_tasks_total: int
    hard_tasks_total: int
    mission3_tasks_total: int
    mission4_tasks_total: int
    mission5_tasks_total: int = 0


class TaskSolvedCreate(BaseModel):
    user_id: int
    task_global_id: int


class SQLResponse(BaseModel):
    columns: List[str]
    data: List[List[Any]]
    row_count: int


class SQLRequest(BaseModel):
    sql_query: str


class ValidationResult(BaseModel):
    is_correct: bool
    message: Optional[str] = None


class TaskShortInfo(BaseModel):
    task_id: int
    task_global_id: int
    title: str
    is_solved: bool
    user_solution: Optional[str] = None


class MissionsResponse(BaseModel):
    missions: Dict[int, List[TaskShortInfo]]


class SolvedTasksResponse(BaseModel):
    solved_missions: Dict[int, List[TaskShortInfo]]


class TaskWithStatus(BaseModel):
    task_id: int
    task_global_id: int
    mission_id: int


class TaskWithStatusResponse(BaseModel):
    task_id: int
    mission_id: int
    title: str
    description: str
    is_solved: bool
    user_solution: Optional[str] = None
    has_clue1: bool
    has_clue2: bool
    previous: dict
    next: dict
    difficulty: Optional[str] = None


class AchievementAward(BaseModel):
    achievement_id: int
    name: str
    description: str
    icon: str


class TaskSubmissionResult(BaseModel):
    was_solved_before: bool
    points_earned: int
    points_penalty: int
    message: str
    is_correct: bool
    awarded_achievements: list[AchievementAward]
    current_points: int
    hint: str = ""
    columns: Optional[list] = None
    data: Optional[list] = None

class DatabaseSchemaNodeColumn(BaseModel):
    title: str
    type: str
    description: Optional[str] = None


class DatabaseSchemaNodeData(BaseModel):
    label: str
    description: str
    columns: List[DatabaseSchemaNodeColumn]


class DatabaseSchemaNodePosition(BaseModel):
    x: float
    y: float


class DatabaseSchemaNode(BaseModel):
    id: str
    position: DatabaseSchemaNodePosition
    type: str = "databaseSchema"
    data: DatabaseSchemaNodeData


class DatabaseSchemaEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str


class DatabaseSchemaResponse(BaseModel):
    nodes: List[DatabaseSchemaNode]
    edges: List[DatabaseSchemaEdge]

