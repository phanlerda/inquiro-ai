from pydantic import BaseModel

class ChatRequest(BaseModel):
    """
    Schema cho yêu cầu đầu vào của endpoint chat.
    """
    query: str
    document_id: int | None = None # Tùy chọn: chỉ chat với một document cụ thể

class ChatResponse(BaseModel):
    """
    Schema cho phản hồi (nếu không streaming).
    Chúng ta sẽ không dùng trực tiếp khi streaming, nhưng nó hữu ích cho việc định nghĩa.
    """
    answer: str
    context: list[str]