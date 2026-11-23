import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized("Требуется аутентификация")
    try:
        username = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _unauthorized("Недействительный или просроченный токен")
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise _unauthorized("Пользователь не найден")
    return user
