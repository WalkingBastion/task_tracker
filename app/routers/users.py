from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_current_user
from app.schemas import UserOut

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[UserOut], summary="Список пользователей")
def list_users(db: Session = Depends(get_db)):
    return crud.list_users(db)
