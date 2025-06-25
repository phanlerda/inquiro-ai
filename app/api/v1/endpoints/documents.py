# backend/app/api/v1/endpoints/documents.py

import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....api import deps
from ....core.ingestion import process_document_and_embed

router = APIRouter()

# Tạo thư mục để lưu trữ file tạm thời
STORAGE_PATH = Path("storage/")
STORAGE_PATH.mkdir(exist_ok=True)

# Định nghĩa các loại file được chấp nhận
ALLOWED_CONTENT_TYPES = ["application/pdf"]

@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user), # <-- Yêu cầu xác thực
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload một tài liệu PDF.
    - Yêu cầu người dùng phải đăng nhập.
    - Chỉ người dùng đã xác thực mới có thể upload.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Loại file không hợp lệ. Chỉ chấp nhận file PDF. (Đã nhận: {file.content_type})"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    # Tạo một tên file duy nhất để tránh ghi đè, có thể thêm user_id hoặc timestamp
    # Ví dụ: unique_filename = f"{current_user.id}_{int(time.time())}_{file.filename}"
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
    
    # Tạo document và gán owner_id là id của người dùng hiện tại
    db_document = crud.crud_document.create_document(
        db=db, document_in=document_in, owner_id=current_user.id
    )
    
    background_tasks.add_task(process_document_and_embed, document_id=db_document.id)

    return db_document