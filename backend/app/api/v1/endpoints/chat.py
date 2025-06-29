# backend/app/api/v1/endpoints/chat.py

from fastapi import APIRouter, Depends
from ....schemas.chat import ChatRequest, ChatResponse
from ....core.rag import get_agentic_rag_response
from ....api import deps
from .... import models

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_with_document(
    request: ChatRequest,
    current_user: models.User = Depends(deps.get_current_user) # <-- Yêu cầu xác thực
):
    """
    Endpoint chính để chat với tài liệu.
    - Yêu cầu người dùng phải đăng nhập.
    - Sẽ tự động lọc để người dùng chỉ có thể chat với tài liệu của chính họ.
    """
    response_data = await get_agentic_rag_response(
        query=request.query, 
        history=request.history,
        document_id=request.document_id,
        user_id=current_user.id # <-- Truyền user_id vào logic RAG
    )
    
    return ChatResponse(**response_data)