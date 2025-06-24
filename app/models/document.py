import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum
from ..db.base_class import Base

class DocumentStatus(enum.Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    filepath = Column(String, unique=True, nullable=False) # Đường dẫn tới file trong object storage
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Sẽ thêm user_id ở các bước sau
    # user_id = Column(Integer, ForeignKey("users.id"))
    # owner = relationship("User", back_populates="documents")