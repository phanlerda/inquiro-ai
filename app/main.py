# backend/app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

# Các import cần thiết cho logic chính
from .core.llm import get_llm
from .db.session import SessionLocal
from .db.init_db import init_db
from .core.ingestion import ensure_qdrant_collection_exists
from .api.v1.endpoints import documents, chat, auth 
from fastapi import APIRouter # Đảm bảo APIRouter được import

# Sử dụng Lifespan context manager để xử lý các tác vụ khởi động và tắt
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Server đang khởi động ---")
    print("Đang khởi tạo database...")
    init_db(db=SessionLocal())
    print("Khởi tạo database thành công.")
    print("Đang khởi tạo Qdrant collection...")
    ensure_qdrant_collection_exists()
    print("Khởi tạo Qdrant collection thành công.")
    print("Đang khởi tạo LLM...")
    app.state.llm = get_llm()
    if app.state.llm is None:
        # Trong môi trường production, bạn có thể muốn ghi log lỗi thay vì raise
        # Hoặc có một cơ chế retry/fallback
        print("LỖI NGHIÊM TRỌNG: Không thể khởi tạo LLM. Kiểm tra API key và cấu hình.")
        # raise RuntimeError("Không thể khởi tạo LLM. Vui lòng kiểm tra API key và cấu hình.")
    else:
        print("Khởi tạo LLM thành công.")
    print("--- Server đã sẵn sàng ---")
    yield
    print("--- Server đang tắt ---")

# Khởi tạo ứng dụng FastAPI với lifespan
# Bỏ hoàn toàn openapi_extra
app = FastAPI(
    title="RAG Fullstack API",
    description="API cho ứng dụng RAG Chatbot toàn diện",
    version="1.0.0",
    lifespan=lifespan
)

# Khai báo api_router
api_router = APIRouter() 

# Bao gồm các router từ API vào api_router
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Include api_router vào app chính
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Chào mừng đến với RAG Fullstack API! Truy cập /docs để xem tài liệu API."}