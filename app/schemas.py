from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.constants import TaskPriority, TaskStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str


class LoginRequest(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class TaskCreate(BaseModel):
    title: Title
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.MEDIUM
    topic_id: int | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: Title | None = None
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    topic_id: int | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None

    @field_validator("title", "status", "priority")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Значение не может быть пустым")
        return value


class StatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    topic: TopicOut | None
    assignee: UserOut | None
    author: UserOut


class TaskList(BaseModel):
    items: list[TaskOut]
    total: int
    limit: int
    offset: int
