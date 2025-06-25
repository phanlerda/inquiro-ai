# backend/app/models/document.py

import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class DocumentStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    """
    Model SQLAlchemy đại diện cho một tài liệu được upload.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    filepath = Column(String, unique=True, nullable=False)
    
    status = Column(
        Enum(DocumentStatus, name="documentstatus_enum", create_constraint=True), 
        nullable=False, 
        default=DocumentStatus.UPLOADING
    )
    
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # --- THAY ĐỔI QUAN TRỌNG ---
    # Thêm cột owner_id để lưu khóa ngoại, trỏ đến id của người dùng trong bảng 'users'
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tạo mối quan hệ "nhiều-một" với model User.
    # 'back_populates' phải khớp với tên relationship trong model User.
    owner = relationship("User", back_populates="documents")