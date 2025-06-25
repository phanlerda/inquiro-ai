from fastapi import APIRouter
from ....schemas.chat import ChatRequest, ChatResponse
from ....core.rag import get_agentic_rag_response

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    response_data = await get_agentic_rag_response( # <-- Gọi hàm agent
        query=request.query, 
        history=request.history,
        document_id=request.document_id
    )
    return ChatResponse(**response_data)