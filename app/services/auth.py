from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.database import get_db
from app.models.models import User

# Конфигурация безопасности
SECRET_KEY = "your-secret-key-change-in-production-min-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


# ==================== ХЕШИРОВАНИЕ ПАРОЛЕЙ ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с помощью bcrypt.
    """
    # Обрезаем пароль до 72 символов (по требованию bcrypt)
    # Если пароль длиннее 72 символов, используется только первая часть.
    # Мы кодируем его в байты перед обрезкой, хотя в большинстве случаев
    # обрезка строки достаточна для ASCII/UTF-8.
    password_bytes = password.encode('utf-8')
    truncated_password = password_bytes[:72]

    # Генерация соли и хеширование
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(truncated_password, salt)

    # Возвращаем хеш в виде строки
    return hash_bytes.decode('utf-8')


# ==================== JWT ТОКЕНЫ ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


# ==================== ЗАВИСИМОСТИ ДЛЯ АУТЕНТИФИКАЦИИ ====================

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Проверка активности пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


async def get_current_admin(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Проверка прав администратора"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user