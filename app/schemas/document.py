from pydantic import BaseModel
from datetime import datetime
from ..models.document import DocumentStatus

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    filepath: str

class DocumentResponse(DocumentBase):
    id: int
    filepath: str
    status: DocumentStatus
    created_at: datetime

    class Config:
        from_attributes = True # Cho phép Pydantic đọc dữ liệu từ các thuộc tính của object (ORM model)