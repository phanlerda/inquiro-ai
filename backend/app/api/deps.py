# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Chỉ cần import cái này
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .. import models, schemas, crud # Đảm bảo các import này đúng
from ..config import settings
from ..db.session import SessionLocal

# Định nghĩa scheme xác thực - ĐÂY LÀ CHỖ QUAN TRỌNG NHẤT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) # Sử dụng oauth2_scheme ở đây
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        # Không cần TokenData ở đây nếu chỉ lấy email
    except JWTError:
        raise credentials_exception
    
    user = crud.crud_user.get_user_by_email(db, email=email) # Sửa lại cách lấy email
    if user is None:
        raise credentials_exception
    return user