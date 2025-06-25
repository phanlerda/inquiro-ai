# backend/app/schemas/chat.py

from pydantic import BaseModel, Field
from typing import List, Tuple

# ==============================================================================
# SCHEMAS CHO YÊU CẦU (REQUEST)
# ==============================================================================

class ChatRequest(BaseModel):
    """
    Schema cho yêu cầu đầu vào của endpoint chat.
    """
    query: str = Field(
        ..., 
        description="Câu hỏi của người dùng.",
        examples=["Dự án Helios-V là gì?"]
    )
    
    history: List[Tuple[str, str]] = Field(
        default=[], 
        description="Lịch sử của cuộc trò chuyện, mỗi phần tử là một cặp (câu hỏi của người dùng, câu trả lời của bot).",
        examples=[[("Dự án đầu tiên là gì?", "Đó là dự án Helios-V."), ("Nó có mục tiêu gì?", "Mục tiêu là khai thác năng lượng mặt trời.")]]
    )
    
    document_id: int | None = Field(
        default=None, 
        description="(Tùy chọn) ID của tài liệu cụ thể muốn chat. Nếu là None, sẽ tìm kiếm trên tất cả các tài liệu."
    )

# ==============================================================================
# SCHEMAS CHO PHẢN HỒI (RESPONSE)
# ==============================================================================

class Source(BaseModel):
    """
    Schema cho một nguồn (chunk) được trích dẫn.
    Đây là thông tin về một đoạn văn bản cụ thể đã được dùng để tạo câu trả lời.
    """
    document_id: int = Field(..., description="ID của tài liệu chứa nguồn này.")
    filename: str = Field(..., description="Tên file của tài liệu gốc.")
    text: str = Field(..., description="Nội dung của chunk văn bản được truy xuất.")
    
    class Config:
        # Cho phép Pydantic đọc dữ liệu từ các thuộc tính của object khác (như dict)
        from_attributes = True


class ChatResponse(BaseModel):
    """
    Schema cho phản hồi cuối cùng của API chat, bao gồm cả câu trả lời và nguồn trích dẫn.
    """
    answer: str = Field(..., description="Câu trả lời do LLM tạo ra, có thể chứa các trích dẫn dạng [Nguồn x].")
    sources: List[Source] = Field(..., description="Danh sách các nguồn (chunks) đã được sử dụng để tạo ra câu trả lời.")