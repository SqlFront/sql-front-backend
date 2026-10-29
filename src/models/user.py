from sqlalchemy import Column, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer, Identity(start=1, increment=1), primary_key=True, index=True
    )
    login = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    fullname = Column(String, nullable=True)
    group = Column(String, nullable=True)
    total_score = Column(Integer, default=0)

    password_rel = relationship(
        "PasswordHash",
        back_populates="user_rel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    achievements = relationship(
        "UsersAchievements", back_populates="user", cascade="all, delete-orphan"
    )
    achievement_progress = relationship(
        "UserAchievementProgress", back_populates="user", cascade="all, delete-orphan"
    )
    solved_tasks = relationship("TaskSolved", back_populates="user")
    quest_progress = relationship("UserQuestProgress", back_populates="user")

    def __str__(self) -> str:
        if self.login:
            grp = f" [{self.group}]" if self.group else ""
            return f"{self.login}{grp}"
        return f"User #{self.user_id}"


class PasswordHash(Base):
    __tablename__ = "password_hashes"

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
    )
    password_hash = Column(String, nullable=False)

    user_rel = relationship("User", back_populates="password_rel")
