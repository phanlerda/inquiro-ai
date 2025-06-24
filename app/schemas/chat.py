from pydantic import BaseModel
from typing import List, Tuple

class ChatRequest(BaseModel):
    """
    Schema cho yêu cầu đầu vào của endpoint chat, giờ đã có lịch sử.
    """
    query: str
    # Lịch sử chat, mỗi phần tử là một cặp (câu hỏi của người dùng, câu trả lời của bot)
    history: List[Tuple[str, str]] = []
    document_id: int | None = None # Tùy chọn: chỉ chat với một document cụ thể

class ChatResponse(BaseModel):
    """
    Schema cho phản hồi (nếu không streaming).
    Chúng ta sẽ không dùng trực tiếp khi streaming, nhưng nó hữu ích cho việc định nghĩa.
    """
    answer: str
    context: list[str]