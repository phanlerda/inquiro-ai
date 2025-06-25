# backend/app/crud/crud_document.py

from sqlalchemy.orm import Session
from .. import models, schemas

def create_document(db: Session, document_in: schemas.DocumentCreate, owner_id: int) -> models.Document:
    """
    Tạo một document mới và gán nó cho một người dùng (owner).
    """
    db_document = models.Document(
        filename=document_in.filename,
        filepath=document_in.filepath,
        status=models.DocumentStatus.UPLOADING,
        owner_id=owner_id # <-- Gán owner_id
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