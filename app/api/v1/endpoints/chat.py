# backend/app/api/v1/endpoints/chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ....schemas.chat import ChatRequest
from ....core.rag import get_rag_response_stream

router = APIRouter()

@router.post("/")
async def chat_with_document(request: ChatRequest):
    """
    Endpoint chính để chat với tài liệu.
    Nhận câu hỏi và trả về câu trả lời được stream theo thời gian thực.
    """
    
    # Gọi hàm xử lý RAG và stream kết quả
    response_stream = get_rag_response_stream(
        query=request.query, 
        document_id=request.document_id
    )
    
    # Trả về một StreamingResponse
    return StreamingResponse(response_stream, media_type="text/plain")