from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class UserEvent(Base):
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user_id = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, index=True
    )
    task_id = Column(Integer, nullable=True, index=True)  # Может быть NULL

    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSON, default={})

    user = relationship(
        "User",
        foreign_keys=[user_id],
        primaryjoin="UserEvent.user_id == User.user_id",
        lazy="selectin",
    )
