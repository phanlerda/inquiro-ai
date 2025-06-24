from sqlalchemy.orm import Session
from .. import models, schemas

def create_document(db: Session, document_in: schemas.DocumentCreate) -> models.Document:
    # SỬA Ở ĐÂY: Sử dụng `document_in` thay vì `document`
    db_document = models.Document(
        filename=document_in.filename,
        filepath=document_in.filepath,
        status=models.DocumentStatus.UPLOADING 
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document