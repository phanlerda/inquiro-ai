import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum, Text
from ..db.base_class import Base

class DocumentStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    filepath = Column(String, unique=True, nullable=False)
    
    # Đảm bảo phần này được viết đầy đủ, không có dấu "..."
    status = Column(
        Enum(DocumentStatus, name="documentstatus_enum", create_constraint=True), 
        nullable=False, 
        default=DocumentStatus.UPLOADING
    )
    
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())