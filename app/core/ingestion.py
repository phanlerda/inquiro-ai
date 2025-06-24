# backend/app/core/ingestion.py

import fitz  # PyMuPDF
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient, models as qdrant_models
from sentence_transformers import SentenceTransformer

# Import các thành phần cần thiết từ ứng dụng của bạn
from .. import crud
from .. import models as db_models
from ..config import settings
from ..db.session import SessionLocal

# --- KHỞI TẠO CÁC THÀNH PHẦN MỘT LẦN ---
# Điều này giúp tái sử dụng model và client, tiết kiệm bộ nhớ và thời gian khởi tạo.
# Việc này được thực hiện khi module được import lần đầu tiên (khi server khởi động).
try:
    print("Đang tải Embedding Model...")
    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    print("Tải Embedding Model thành công.")
    
    print("Đang kết nối tới Qdrant...")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    print("Kết nối Qdrant thành công.")

except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG khi khởi tạo các thành phần Ingestion: {e}")
    embedding_model = None
    qdrant_client = None

def ensure_qdrant_collection_exists():
    """
    Đảm bảo collection trong Qdrant tồn tại. Nếu chưa có, tạo mới.
    Hàm này được gọi một lần khi server FastAPI khởi động.
    """
    if not qdrant_client or not embedding_model:
        print("Bỏ qua việc kiểm tra collection do Qdrant client hoặc embedding model chưa được khởi tạo.")
        return
        
    try:
        qdrant_client.get_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
        print(f"Collection '{settings.QDRANT_COLLECTION_NAME}' đã tồn tại.")
    except Exception:
        print(f"Collection '{settings.QDRANT_COLLECTION_NAME}' không tồn tại. Đang tạo mới...")
        
        # Lấy kích thước vector từ model
        embedding_size = embedding_model.get_sentence_embedding_dimension()
        if not isinstance(embedding_size, int):
             raise ValueError("Không thể xác định kích thước embedding từ model.")

        qdrant_client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(
                size=embedding_size,
                distance=qdrant_models.Distance.COSINE
            )
        )
        print(f"Tạo collection '{settings.QDRANT_COLLECTION_NAME}' với kích thước vector {embedding_size} thành công.")


def process_document_and_embed(document_id: int):
    """
    Tác vụ nền chính được gọi bởi FastAPI BackgroundTasks.
    Hàm này sẽ tự quản lý DB session của riêng nó.
    
    Quy trình:
    1. Lấy thông tin document từ DB.
    2. Đọc file PDF.
    3. Chia thành các chunks.
    4. Tạo embeddings cho các chunks.
    5. Lưu embeddings vào Qdrant.
    6. Cập nhật trạng thái document trong DB.
    """
    print(f"BACKGROUND TASK: Bắt đầu xử lý document ID: {document_id}")
    
    # Tạo một DB session mới chỉ dành cho tác vụ nền này
    db: Session = SessionLocal()
    
    try:
        # Kiểm tra lại các thành phần cốt lõi
        if not embedding_model or not qdrant_client:
            raise RuntimeError("Lỗi: Embedding model hoặc Qdrant client chưa được khởi tạo.")

        # 1. Lấy thông tin document từ DB
        db_document = crud.crud_document.get_document(db, document_id=document_id)
        if not db_document:
            raise FileNotFoundError(f"Không tìm thấy document với ID {document_id} trong database.")

        # Cập nhật trạng thái là PROCESSING
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.PROCESSING)

        # 2. Đọc file PDF
        print(f"Đang đọc file: {db_document.filepath}")
        doc = fitz.open(db_document.filepath)
        full_text = "".join(page.get_text("text") for page in doc)
        doc.close()

        # 3. Chia thành các chunks (logic đơn giản, có thể cải tiến sau)
        # Ví dụ: chia theo đoạn văn bản được ngăn cách bởi hai lần xuống dòng
        chunks = [chunk.strip() for chunk in full_text.split('\n\n') if chunk.strip()]
        if not chunks:
            print(f"Cảnh báo: Tài liệu {db_document.filename} không có nội dung hoặc không thể chia chunks.")
            crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.FAILED)
            return
            
        print(f"Tài liệu được chia thành {len(chunks)} chunks.")

        # 4. Tạo embeddings
        print(f"Đang tạo embeddings cho {len(chunks)} chunks...")
        embeddings = embedding_model.encode(chunks, show_progress_bar=True, batch_size=32)
        
        # 5. Lưu vào Qdrant
        print("Đang lưu các vectors vào Qdrant...")
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                qdrant_models.PointStruct(
                    id=f"{document_id}-{i}", # ID duy nhất cho mỗi chunk
                    vector=embedding.tolist(),
                    payload={
                        "document_id": document_id,
                        "filename": db_document.filename,
                        "text": chunk
                    }
                )
                for i, (embedding, chunk) in enumerate(zip(embeddings, chunks))
            ],
            wait=True # Đợi cho đến khi quá trình upsert hoàn tất
        )
        
        print(f"Lưu thành công {len(chunks)} vector vào Qdrant.")
        
        # 6. Cập nhật trạng thái COMPLETED
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.COMPLETED)
        print(f"BACKGROUND TASK: Hoàn tất xử lý document ID: {document_id}")

    except Exception as e:
        print(f"LỖI trong tác vụ nền khi xử lý document ID {document_id}: {e}")
        # Cập nhật trạng thái FAILED trong DB
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.FAILED)

    finally:
        # Đảm bảo DB session luôn được đóng sau khi tác vụ hoàn thành hoặc gặp lỗi
        print(f"BACKGROUND TASK: Đóng DB session cho document ID: {document_id}")
        db.close()