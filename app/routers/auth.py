from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, Token, UserCreate, UserOut
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserOut, status_code=201, summary="Регистрация")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, payload.username) is not None:
        raise HTTPException(status_code=409, detail="Пользователь с таким именем уже существует")
    return crud.create_user(db, payload.username, payload.full_name, hash_password(payload.password))


@router.post("/login", response_model=Token, summary="Вход")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, payload.username)
    if user is None:
        verify_password(payload.password, DUMMY_HASH)
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    return Token(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserOut, summary="Текущий пользователь")
def me(user: User = Depends(get_current_user)):
    return user
