import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics import build_dataframe
from app.models import Task, Topic, User


def load_tasks_dataframe(db: Session) -> pd.DataFrame:
    stmt = (
        select(
            Task.id,
            Task.status,
            Task.priority,
            Task.due_date,
            Task.created_at,
            Task.completed_at,
            Topic.name,
            User.full_name,
        )
        .select_from(Task)
        .outerjoin(Topic, Task.topic_id == Topic.id)
        .outerjoin(User, Task.assignee_id == User.id)
    )
    rows = [tuple(row) for row in db.execute(stmt)]
    return build_dataframe(rows)
