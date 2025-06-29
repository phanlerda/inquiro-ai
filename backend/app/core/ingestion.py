# backend/app/core/ingestion.py

import uuid
import numpy as np
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from unstructured.partition.pdf import partition_pdf

from .. import crud, models as db_models
from ..config import settings
from ..db.session import SessionLocal

# --- KHỞI TẠO CÁC THÀNH PHẦN MỘT LẦN ---
try:
    print("Đang tải Dense Embedding Model (Semantic Search)...")
    dense_embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    print("Tải Dense Embedding Model thành công.")
    
    print("Đang tải Sparse Embedding Model (Keyword Search)...")
    sparse_embedding_model = SentenceTransformer(settings.SPARSE_VECTOR_MODEL_NAME)
    print("Tải Sparse Embedding Model thành công.")
    
    print("Đang kết nối tới Qdrant...")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    print("Kết nối Qdrant thành công.")

except Exception as e:
    print(f"Lỗi nghiêm trọng khi khởi tạo các thành phần Ingestion: {e}")
    dense_embedding_model = None
    sparse_embedding_model = None
    qdrant_client = None

def ensure_qdrant_collection_exists():
    """
    Đảm bảo collection trong Qdrant tồn tại.
    Nếu chưa có, tạo mới. Nếu đã có, không làm gì cả.
    """
    if not qdrant_client:
        raise ConnectionError("Qdrant client chưa được khởi tạo.")
    
    try:
        # Thử lấy thông tin của collection. Nếu thành công, nghĩa là nó đã tồn tại.
        qdrant_client.get_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
        print(f"Collection '{settings.QDRANT_COLLECTION_NAME}' đã tồn tại. Bỏ qua việc tạo mới.")
    except Exception as e:
        # Nếu có lỗi (thường là lỗi 404 Not Found), nghĩa là collection chưa tồn tại.
        print(f"Collection '{settings.QDRANT_COLLECTION_NAME}' không tồn tại. Đang tạo mới...")
        
        if not dense_embedding_model:
            raise ValueError("Dense embedding model chưa được khởi tạo.")
            
        # Chỉ tạo collection khi nó chưa có
        qdrant_client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=dense_embedding_model.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "text": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            }
        )
        print("Tạo collection mới thành công.")
        
def process_document_and_embed(document_id: int):
    """
    Tác vụ nền chính: đọc, chunk, tạo dense & sparse vectors và lưu vào Qdrant.
    """
    db = SessionLocal()
    try:
        print(f"BACKGROUND TASK: Bắt đầu xử lý document ID: {document_id}")
        
        if not all([dense_embedding_model, sparse_embedding_model, qdrant_client]):
            raise ValueError("Lỗi: Một trong các thành phần (dense, sparse, qdrant) chưa được khởi tạo.")

        db_document = crud.crud_document.get_document(db, document_id=document_id)
        if not db_document:
            print(f"Lỗi: Không tìm thấy document với ID {document_id}")
            return
            
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.PROCESSING)

        print(f"Đang phân tích và trích xuất nội dung từ {db_document.filepath} bằng unstructured...")
        elements = partition_pdf(filename=db_document.filepath, infer_table_structure=True)
        full_text = "\n\n".join([str(el) for el in elements])

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100, length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(full_text)

        if not chunks:
            print(f"Cảnh báo: Tài liệu {db_document.filename} không có nội dung hoặc không thể chia chunks.")
            crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.FAILED, reason="No content to process")
            return
            
        print(f"Tài liệu được chia thành {len(chunks)} chunks.")

        print("Đang tạo dense vectors (embeddings)...")
        dense_embeddings = dense_embedding_model.encode(chunks, show_progress_bar=True)
        
        print("Đang tạo sparse vectors...")
        sparse_embeddings_raw = sparse_embedding_model.encode(chunks, show_progress_bar=True)

        print("Đang chuẩn bị và lưu các vectors vào Qdrant...")
        points_to_upsert = []
        for i, (dense_embedding, sparse_embedding_raw) in enumerate(zip(dense_embeddings, sparse_embeddings_raw)):
            # Tìm các chỉ số của các phần tử khác không trong sparse vector
            indices = np.where(sparse_embedding_raw > 0)[0].tolist()
            # Lấy các giá trị tương ứng với các chỉ số đó
            values = sparse_embedding_raw[indices].tolist()

            points_to_upsert.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        "dense": dense_embedding.tolist(),
                        "text": models.SparseVector(
                            indices=indices,
                            values=values
                        )
                    },
                    payload={
                        "document_id": document_id,
                        "filename": db_document.filename,
                        "text": chunks[i],
                        "owner_id": db_document.owner_id
                    }
                )
            )

        if points_to_upsert:
            qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points_to_upsert,
                wait=True
            )
            print(f"Lưu thành công {len(points_to_upsert)} vector vào Qdrant.")
        
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.COMPLETED)
        print(f"BACKGROUND TASK: Hoàn tất xử lý document ID: {document_id}")

    except Exception as e:
        print(f"LỖI trong tác vụ nền khi xử lý document ID {document_id}: {e}")
        crud.crud_document.update_document_status(db, document_id=document_id, status=db_models.DocumentStatus.FAILED, reason=str(e))
    finally:
        db.close()
        print(f"BACKGROUND TASK: Đóng DB session cho document ID: {document_id}")