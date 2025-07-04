from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Lớp quản lý cấu hình cho toàn bộ ứng dụng.
    Các giá trị sẽ được đọc từ file .env.
    """
    # Nạp các biến từ file .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    # Cấu hình cho Google Gemini API
    GOOGLE_API_KEY: str

    # Cấu hình cho Database
    DATABASE_URL: str

    # Cấu hình cho Vector DB
    QDRANT_URL: str
    QDRANT_COLLECTION_NAME: str

    # Cấu hình cho Embedding Model
    EMBEDDING_MODEL_NAME: str

    # Cấu hình cho Reranker Model
    RERANKER_MODEL_NAME: str
    
    # Cấu hình cho Sparse Vector Model (Hybrid Search)
    SPARSE_VECTOR_MODEL_NAME: str

    TAVILY_API_KEY: str

    # Thêm các biến JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

# Khởi tạo một đối tượng settings để sử dụng trong toàn bộ ứng dụng
settings = Settings()