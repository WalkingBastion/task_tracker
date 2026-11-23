from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.constants import CLOSED_STATUSES, SortField, SortOrder, TaskPriority, TaskStatus
from app.models import Task, Topic, User
from app.schemas import TaskCreate, TaskUpdate, TopicCreate

TASK_LOAD_OPTIONS = (
    selectinload(Task.topic),
    selectinload(Task.assignee),
    selectinload(Task.author),
)

SORT_COLUMNS = {
    SortField.CREATED_AT: Task.created_at,
    SortField.UPDATED_AT: Task.updated_at,
    SortField.DUE_DATE: Task.due_date,
    SortField.TITLE: Task.title,
}


@dataclass
class TaskFilters:
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    topic_id: int | None = None
    assignee_id: int | None = None
    author_id: int | None = None
    search: str | None = None
    due_before: datetime | None = None
    due_after: datetime | None = None
    overdue_only: bool = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _plain(value):
    return value.value if isinstance(value, Enum) else value


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, username: str, full_name: str, hashed_password: str) -> User:
    user = User(username=username, full_name=full_name, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name, User.id)))


def create_topic(db: Session, payload: TopicCreate) -> Topic:
    exists = db.scalar(select(Topic.id).where(Topic.name == payload.name))
    if exists is not None:
        raise HTTPException(status_code=409, detail="Тема с таким названием уже существует")
    topic = Topic(name=payload.name, description=payload.description)
    db.add(topic)
    db.commit()
    return topic


def list_topics(db: Session) -> list[Topic]:
    return list(db.scalars(select(Topic).order_by(Topic.name)))


def delete_topic(db: Session, topic_id: int) -> None:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Тема не найдена")
    db.execute(update(Task).where(Task.topic_id == topic_id).values(topic_id=None))
    db.delete(topic)
    db.commit()


def _ensure_topic(db: Session, topic_id: int | None) -> None:
    if topic_id is not None and db.get(Topic, topic_id) is None:
        raise HTTPException(status_code=404, detail="Тема не найдена")


def _ensure_assignee(db: Session, user_id: int | None) -> None:
    if user_id is not None and db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="Исполнитель не найден")


def _apply_status(task: Task, status: TaskStatus) -> None:
    task.status = status.value
    task.completed_at = _utcnow() if status == TaskStatus.DONE else None


def get_task(db: Session, task_id: int) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id).options(*TASK_LOAD_OPTIONS))
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


def create_task(db: Session, payload: TaskCreate, author: User) -> Task:
    _ensure_topic(db, payload.topic_id)
    _ensure_assignee(db, payload.assignee_id)
    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        topic_id=payload.topic_id,
        assignee_id=payload.assignee_id,
        author_id=author.id,
        due_date=payload.due_date,
    )
    _apply_status(task, payload.status)
    db.add(task)
    db.commit()
    return task


def update_task(db: Session, task_id: int, payload: TaskUpdate) -> Task:
    task = get_task(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    if "topic_id" in data:
        _ensure_topic(db, data["topic_id"])
    if "assignee_id" in data:
        _ensure_assignee(db, data["assignee_id"])
    if "status" in data:
        _apply_status(task, data.pop("status"))
    for field, value in data.items():
        setattr(task, field, _plain(value))
    db.commit()
    return task


def set_task_status(db: Session, task_id: int, status: TaskStatus) -> Task:
    task = get_task(db, task_id)
    _apply_status(task, status)
    db.commit()
    return task


def delete_task(db: Session, task_id: int, user: User) -> None:
    task = get_task(db, task_id)
    if task.author_id != user.id:
        raise HTTPException(status_code=403, detail="Удалить задачу может только её автор")
    db.delete(task)
    db.commit()


def _conditions(filters: TaskFilters) -> list:
    conditions = []
    if filters.status is not None:
        conditions.append(Task.status == filters.status.value)
    if filters.priority is not None:
        conditions.append(Task.priority == filters.priority.value)
    if filters.topic_id is not None:
        conditions.append(Task.topic_id == filters.topic_id)
    if filters.assignee_id is not None:
        conditions.append(Task.assignee_id == filters.assignee_id)
    if filters.author_id is not None:
        conditions.append(Task.author_id == filters.author_id)
    if filters.search:
        pattern = f"%{escape_like(filters.search)}%"
        conditions.append(
            or_(
                Task.title.ilike(pattern, escape="\\"),
                Task.description.ilike(pattern, escape="\\"),
            )
        )
    if filters.due_before is not None:
        conditions.append(Task.due_date <= filters.due_before)
    if filters.due_after is not None:
        conditions.append(Task.due_date >= filters.due_after)
    if filters.overdue_only:
        conditions.append(Task.due_date < _utcnow())
        conditions.append(Task.status.notin_(CLOSED_STATUSES))
    return conditions


def list_tasks(
    db: Session,
    filters: TaskFilters,
    sort_by: SortField,
    order: SortOrder,
    limit: int,
    offset: int,
) -> tuple[list[Task], int]:
    conditions = _conditions(filters)
    total = db.scalar(select(func.count(Task.id)).where(*conditions)) or 0
    column = SORT_COLUMNS[sort_by]
    ordering = column.asc() if order == SortOrder.ASC else column.desc()
    stmt = (
        select(Task)
        .where(*conditions)
        .options(*TASK_LOAD_OPTIONS)
        .order_by(ordering, Task.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt)), total
