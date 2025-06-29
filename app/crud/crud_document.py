# backend/app/crud/crud_document.py

from sqlalchemy.orm import Session
from typing import List # <-- Đảm bảo đã import List
from .. import models, schemas

def create_document(db: Session, document_in: schemas.DocumentCreate, owner_id: int) -> models.Document:
    db_document = models.Document(
        filename=document_in.filename,
        filepath=document_in.filepath,
        status=models.DocumentStatus.UPLOADING,
        owner_id=owner_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int) -> models.Document | None:
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def update_document_status(
    db: Session, document_id: int, status: models.DocumentStatus, reason: str | None = None
) -> models.Document | None:
    db_document = get_document(db, document_id)
    if db_document:
        db_document.status = status
        db_document.failure_reason = reason
        db.commit()
        db.refresh(db_document)
    return db_document

def delete_document(db: Session, document_id: int) -> models.Document | None:
    db_document = get_document(db, document_id)
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document

# --- HÀM CẦN KIỂM TRA LẠI ---
def get_documents_by_owner(db: Session, owner_id: int) -> List[models.Document]:
    """
    Lấy danh sách tất cả các tài liệu của một người dùng.
    """
    return db.query(models.Document).filter(models.Document.owner_id == owner_id).order_by(models.Document.created_at.desc()).all()