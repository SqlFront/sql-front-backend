from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, index=True)
    task_global_id = Column(
        Integer,
        Identity(start=1, increment=1),
        primary_key=True,
        index=True,
        unique=True,
    )
    mission_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    clue = Column(String, nullable=False)
    correct_query = Column(Text)
    expected_result = Column(JSONB)
    tags = Column(ARRAY(String))

    solved_by = relationship("TaskSolved", back_populates="task")


class TaskSolved(Base):
    __tablename__ = "tasks_solved"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    task_global_id = Column(
        Integer, ForeignKey("tasks.task_global_id"), primary_key=True
    )
    solved_at = Column(DateTime, default=func.now())
    user_query = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="solved_tasks")
    task = relationship("Task", back_populates="solved_by")
