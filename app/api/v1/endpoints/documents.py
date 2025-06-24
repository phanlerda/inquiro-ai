import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

# Import các package đã được tổ chức lại bằng __init__.py
from .... import crud, models, schemas
from ....db.session import SessionLocal

router = APIRouter()

# Tạo một thư mục để lưu trữ file tạm thời, mô phỏng object storage
STORAGE_PATH = Path("storage/")
STORAGE_PATH.mkdir(exist_ok=True)

# Dependency để lấy DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    """
    Upload một tài liệu.
    - Lưu file vào một thư mục cục bộ (mô phỏng object storage).
    - Tạo một record trong database để theo dõi tài liệu.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    # Tạo đường dẫn lưu file an toàn
    saved_filepath = STORAGE_PATH / Path(file.filename).name
    
    try:
        with saved_filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    document_in = schemas.DocumentCreate(
        filename=file.filename,
        filepath=str(saved_filepath)
    )
    
    db_document = crud.crud_document.create_document(db=db, document_in=document_in)
    
    # Cập nhật trạng thái sau khi lưu thành công
    db_document.status = models.document.DocumentStatus.UPLOADING # Hoặc PROCESSING nếu bạn bắt đầu xử lý ngay
    db.commit()
    db.refresh(db_document)

    # Ở đây, chúng ta sẽ kích hoạt một tác vụ nền để xử lý file (ở bước sau)
    # background_tasks.add_task(process_document, document_id=db_document.id)

    return db_document