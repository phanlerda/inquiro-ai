# backend/app/api/v1/endpoints/documents.py

import shutil
from pathlib import Path
import time
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import os
from ....core.rag import delete_vectors_for_document
from typing import List
from .... import crud, models, schemas
from ....api import deps
from ....core.ingestion import process_document_and_embed

router = APIRouter()

# Tạo thư mục để lưu trữ file nếu nó chưa tồn tại
STORAGE_PATH = Path("storage/")
STORAGE_PATH.mkdir(exist_ok=True)

# Định nghĩa các loại file được chấp nhận
ALLOWED_CONTENT_TYPES = ["application/pdf"]

@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload một tài liệu PDF.
    - Yêu cầu người dùng phải đăng nhập.
    - Tự động tạo một tên file duy nhất trên server để tránh trùng lặp.
    - Lưu file vào thư mục cục bộ.
    - Tạo một record trong database để theo dõi.
    - Kích hoạt tác vụ nền để xử lý tài liệu.
    """
    # 1. Kiểm tra loại file
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Loại file không hợp lệ. Chỉ chấp nhận file PDF. (Đã nhận: {file.content_type})"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    # 2. Tạo tên file duy nhất
    # Lấy phần mở rộng của file (ví dụ: .pdf)
    file_extension = Path(file.filename).suffix
    # Tạo tên file mới bằng cách kết hợp timestamp, user_id và một chuỗi ngẫu nhiên ngắn
    # Điều này đảm bảo tên file gần như không thể trùng lặp
    unique_filename = f"{current_user.id}_{int(time.time())}_{uuid.uuid4().hex[:6]}{file_extension}"
    
    saved_filepath = STORAGE_PATH / unique_filename

    # 3. Lưu file vật lý
    try:
        with saved_filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    # 4. Tạo record trong database
    # `filename` sẽ lưu tên file gốc để hiển thị cho người dùng.
    # `filepath` sẽ lưu đường dẫn duy nhất trên server.
    document_in = schemas.DocumentCreate(
        filename=file.filename,
        filepath=str(saved_filepath)
    )
    
    db_document = crud.crud_document.create_document(
        db=db, document_in=document_in, owner_id=current_user.id
    )
    
    # 5. Kích hoạt tác vụ nền
    background_tasks.add_task(process_document_and_embed, document_id=db_document.id)

    return db_document

@router.get("/", response_model=List[schemas.DocumentResponse])
def read_documents(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = 0, # Tùy chọn cho phân trang
    limit: int = 100 # Tùy chọn cho phân trang
):
    """
    Lấy danh sách các tài liệu của người dùng hiện tại.
    """
    documents = crud.crud_document.get_documents_by_owner(db=db, owner_id=current_user.id)
    return documents

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Xóa một tài liệu:
    - Yêu cầu người dùng phải đăng nhập.
    - Chỉ chủ sở hữu mới có thể xóa tài liệu của mình.
    - Xóa file vật lý, các vector liên quan và record trong database.
    """
    db_document = crud.crud_document.get_document(db, document_id=document_id)

    # 1. Kiểm tra xem tài liệu có tồn tại không
    if not db_document:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")

    # 2. Kiểm tra quyền sở hữu
    if db_document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xóa tài liệu này.")

    # 3. Xóa file vật lý
    try:
        if os.path.exists(db_document.filepath):
            os.remove(db_document.filepath)
            print(f"Đã xóa file vật lý: {db_document.filepath}")
    except OSError as e:
        print(f"Lỗi khi xóa file {db_document.filepath}: {e.strerror}")
        # Có thể quyết định dừng lại hoặc tiếp tục xóa dữ liệu khác
        
    # 4. Xóa các vector liên quan trong Qdrant
    delete_vectors_for_document(document_id=document_id)

    # 5. Xóa record trong database PostgreSQL
    crud.crud_document.delete_document(db=db, document_id=document_id)
    
    # Trả về 204 No Content, không cần body
    return