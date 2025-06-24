from sqlalchemy.orm import Session
from .base_class import Base
from .session import engine

def init_db(db: Session) -> None:
    # Tạo tất cả các bảng trong database
    Base.metadata.create_all(bind=engine)