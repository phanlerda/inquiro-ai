# backend/scripts/ingest_system_docs.py

# Import các thư viện cần thiết
import asyncio
from pathlib import Path
import sys
import os

# Thêm thư mục gốc vào Python path để import các module của app
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import các module liên quan đến database, xử lý tài liệu, và schema
from app.db.session import SessionLocal
from app.core.ingestion import process_document_and_embed, ensure_qdrant_collection_exists
from app.crud.crud_document import create_document
from app.schemas.document import DocumentCreate

# Import các module liên quan đến user (tạo user admin nếu chưa có)
from app.models.user import User
from app.crud.crud_user import get_user_by_email, create_user as create_db_user
from app.schemas.user import UserCreate

# Đường dẫn đến thư mục chứa các tài liệu hệ thống
SYSTEM_DOCS_PATH = Path(__file__).resolve().parent / "system_documents"
# Đường dẫn lưu file copy vào storage
STORAGE_PATH_FOR_SYSTEM_DOCS = Path("storage") / "system_docs"

async def ingest_all_system_documents():
    print("--- Bắt đầu Ingest Tài liệu Hệ thống ---")

    # Đảm bảo các thư mục tồn tại
    SYSTEM_DOCS_PATH.mkdir(exist_ok=True)
    STORAGE_PATH_FOR_SYSTEM_DOCS.mkdir(parents=True, exist_ok=True)

    # Khởi tạo các thành phần cần thiết (vì script độc lập)

    from app.core.llm import get_llm # Tải LLM để các module khác có thể dùng
    get_llm()
    
    db = SessionLocal()
    try:
        # Đảm bảo collection Qdrant tồn tại
        ensure_qdrant_collection_exists()

        # Tạo một user "hệ thống" nếu chưa có để gán owner_id
        admin_email = "system@example.com"
        admin_user = get_user_by_email(db, email=admin_email)
        if not admin_user:
            print(f"Tạo người dùng hệ thống: {admin_email}")
            admin_user = create_db_user(db, user=UserCreate(email=admin_email, password="a_very_strong_system_password"))
        
        # Lấy id của user hệ thống để gán owner_id cho tài liệu
        system_owner_id = admin_user.id

        # Lặp qua tất cả các file PDF trong thư mục tài liệu hệ thống
        for pdf_file in SYSTEM_DOCS_PATH.glob("*.pdf"):
            print(f"Đang xử lý file hệ thống: {pdf_file.name}")
            
            # Sao chép file vào thư mục storage (giống luồng upload)
            # Điều này đảm bảo đường dẫn trong DB là nhất quán
            target_filepath = STORAGE_PATH_FOR_SYSTEM_DOCS / pdf_file.name
            with pdf_file.open("rb") as src, target_filepath.open("wb") as dst:
                dst.write(src.read())

            # Tạo record trong database
            doc_create = DocumentCreate(filename=pdf_file.name, filepath=str(target_filepath))
            # Sử dụng owner_id của admin hoặc để None
            db_document = create_document(db=db, document_in=doc_create, owner_id=system_owner_id) 
            
            print(f"Đã tạo record cho {pdf_file.name} với ID: {db_document.id}, owner_id: {system_owner_id}")

            # Chạy tác vụ nền (trong trường hợp này, chúng ta chạy trực tiếp vì đây là script)
            # Bạn có thể muốn chạy process_document_and_embed trong một tiến trình riêng nếu có nhiều file
            await asyncio.to_thread(process_document_and_embed, document_id=db_document.id)
            print(f"Hoàn tất ingest cho file: {pdf_file.name}")

    finally:
        db.close()
    
    print("--- Hoàn tất Ingest Tài liệu Hệ thống ---")

if __name__ == "__main__":
    # Cần load dotenv để các biến môi trường (như API key) được nạp
    from dotenv import load_dotenv
    # Xác định đường dẫn đến file .env từ thư mục gốc của backend
    dotenv_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=dotenv_path)
    
    # Chạy hàm ingest tài liệu hệ thống bằng asyncio
    asyncio.run(ingest_all_system_documents())