from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import TaskPriority, TaskStatus
from app.database import Base


def _in_clause(column: str, enum_cls) -> str:
    values = ", ".join(f"'{item.value}'" for item in enum_cls)
    return f"{column} IN ({values})"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    full_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    tasks: Mapped[list["Task"]] = relationship(back_populates="topic")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(_in_clause("status", TaskStatus), name="ck_tasks_status"),
        CheckConstraint(_in_clause("priority", TaskPriority), name="ck_tasks_priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.NEW.value,
        server_default=TaskStatus.NEW.value,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=TaskPriority.MEDIUM.value,
        server_default=TaskPriority.MEDIUM.value,
    )
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    topic: Mapped[Topic | None] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    author: Mapped[User] = relationship(foreign_keys=[author_id])
