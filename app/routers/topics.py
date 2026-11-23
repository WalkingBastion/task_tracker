from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_current_user
from app.schemas import TopicCreate, TopicOut

router = APIRouter(
    prefix="/topics",
    tags=["Темы"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TopicOut, status_code=201, summary="Создать тему")
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    return crud.create_topic(db, payload)


@router.get("", response_model=list[TopicOut], summary="Список тем")
def list_topics(db: Session = Depends(get_db)):
    return crud.list_topics(db)


@router.delete("/{topic_id}", status_code=204, summary="Удалить тему")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    crud.delete_topic(db, topic_id)
    return Response(status_code=204)
