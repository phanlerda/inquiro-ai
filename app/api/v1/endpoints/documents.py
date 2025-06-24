import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from .... import crud, schemas
from ....db.session import SessionLocal
from ....core.ingestion import process_document_and_embed

# Khởi tạo router
router = APIRouter()

# Tạo một thư mục để lưu trữ file tạm thời, mô phỏng object storage
STORAGE_PATH = Path("storage/")
STORAGE_PATH.mkdir(exist_ok=True)

# Dependency để lấy DB session cho mỗi request
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload một tài liệu lên hệ thống.

    - **Lưu file vật lý:** File sẽ được lưu vào một thư mục cục bộ (`/storage`) 
      để mô phỏng việc lưu trữ trên một object storage như S3.
    
    - **Tạo bản ghi trong DB:** Một bản ghi mới sẽ được tạo trong bảng `documents` 
      để theo dõi trạng thái và metadata của file.
      
    - **Kích hoạt xử lý nền:** Một tác vụ nền sẽ được kích hoạt ngay lập tức 
      để đọc, chunk, và tạo embeddings cho tài liệu. API sẽ trả về phản hồi 
      ngay lập tức mà không cần chờ quá trình này hoàn tất.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    # Tạo đường dẫn lưu file an toàn, tránh các ký tự đặc biệt trong tên file
    # và đảm bảo file được lưu trong thư mục STORAGE_PATH
    saved_filepath = STORAGE_PATH / Path(file.filename).name
    
    try:
        # Lưu file từ request vào đường dẫn đã tạo
        with saved_filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        # Luôn đóng file sau khi xử lý xong
        file.file.close()
        
    # Tạo một đối tượng Pydantic schema để truyền vào hàm CRUD
    document_in = schemas.DocumentCreate(
        filename=file.filename,
        filepath=str(saved_filepath)
    )
    
    # Gọi hàm CRUD để tạo bản ghi document trong database
    db_document = crud.crud_document.create_document(db=db, document_in=document_in)
    
    # Thêm tác vụ xử lý tài liệu vào hàng đợi tác vụ nền của FastAPI.
    # Tác vụ này sẽ chạy sau khi response đã được gửi đi.
    # Chúng ta chỉ truyền `document_id` để tác vụ nền có thể tự lấy thông tin
    # và tạo DB session riêng của nó.
    background_tasks.add_task(process_document_and_embed, document_id=db_document.id)

    # Trả về thông tin của document vừa được tạo trong DB
    return db_document