from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import crud
from app.constants import SortField, SortOrder, TaskPriority, TaskStatus
from app.crud import TaskFilters
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import StatusUpdate, TaskCreate, TaskList, TaskOut, TaskUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["Задачи"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TaskOut, status_code=201, summary="Создать задачу")
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_task(db, payload, user)


@router.get("", response_model=TaskList, summary="Список задач с фильтрацией")
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    topic_id: int | None = None,
    assignee_id: int | None = None,
    author_id: int | None = None,
    search: str | None = Query(default=None, max_length=100),
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    overdue_only: bool = False,
    sort_by: SortField = SortField.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = TaskFilters(
        status=status,
        priority=priority,
        topic_id=topic_id,
        assignee_id=assignee_id,
        author_id=author_id,
        search=search,
        due_before=due_before,
        due_after=due_after,
        overdue_only=overdue_only,
    )
    items, total = crud.list_tasks(db, filters, sort_by, order, limit, offset)
    return TaskList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TaskOut, summary="Получить задачу")
def get_task(task_id: int, db: Session = Depends(get_db)):
    return crud.get_task(db, task_id)


@router.put("/{task_id}", response_model=TaskOut, summary="Обновить задачу")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    return crud.update_task(db, task_id, payload)


@router.patch("/{task_id}/status", response_model=TaskOut, summary="Изменить статус задачи")
def update_status(task_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    return crud.set_task_status(db, task_id, payload.status)


@router.delete("/{task_id}", status_code=204, summary="Удалить задачу")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    crud.delete_task(db, task_id, user)
    return Response(status_code=204)
