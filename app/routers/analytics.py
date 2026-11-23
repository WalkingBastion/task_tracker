from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.analytics import build_summary, group_counts, render_chart
from app.constants import GroupBy
from app.data import load_tasks_dataframe
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["Аналитика"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", summary="Сводная статистика по задачам")
def summary(db: Session = Depends(get_db)):
    return build_summary(load_tasks_dataframe(db))


@router.get("/group", summary="Группировка задач по статусу, теме или исполнителю")
def group(group_by: GroupBy = GroupBy.STATUS, db: Session = Depends(get_db)):
    df = load_tasks_dataframe(db)
    return {"group_by": group_by.value, "items": group_counts(df, group_by)}


@router.get("/chart", summary="График распределения задач (PNG)")
def chart(group_by: GroupBy = GroupBy.STATUS, db: Session = Depends(get_db)):
    df = load_tasks_dataframe(db)
    return Response(content=render_chart(df, group_by), media_type="image/png")
