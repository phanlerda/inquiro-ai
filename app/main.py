from fastapi import FastAPI
from .core.llm import get_llm

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="RAG Fullstack API",
    description="API cho ứng dụng RAG Chatbot toàn diện",
    version="1.0.0",
)

# Khởi tạo LLM một lần khi ứng dụng khởi động để tái sử dụng
llm = get_llm()

@app.get("/", tags=["Root"])
async def read_root():
    """
    Endpoint gốc để kiểm tra API có hoạt động không.
    """
    return {"message": "Chào mừng đến với RAG Fullstack API!"}

@app.post("/test-gemini/", tags=["Tests"])
async def test_gemini(prompt: str):
    """
    Endpoint để kiểm tra tích hợp với Gemini 1.5 Flash.
    Gửi một prompt và nhận lại phản hồi từ model.
    """
    try:
        response = llm.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}