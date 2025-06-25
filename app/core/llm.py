# backend/app/core/llm.py

from langchain_google_genai import ChatGoogleGenerativeAI
import os
from ..config import settings

# LangChain đọc API key từ biến môi trường
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

def get_llm():
    """
    Khởi tạo và trả về một instance LLM của LangChain cho model Gemini.
    """
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.5,
            top_p=1,
            top_k=1,
            # LangChain tự động quản lý safety settings, nhưng có thể cấu hình nếu cần
            convert_system_message_to_human=True # Giúp tương thích tốt hơn với các prompt
        )
        return model
    except Exception as e:
        print(f"Lỗi khi khởi tạo LangChain ChatGoogleGenerativeAI: {e}")
        return None