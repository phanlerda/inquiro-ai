from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from ..config import settings
from .llm import get_llm

# --- KHỞI TẠO CÁC THÀNH PHẦN MỘT LẦN ---
# Tái sử dụng các client và model đã được khởi tạo trong các module khác nếu có thể,
# hoặc khởi tạo lại ở đây để module này độc lập.
try:
    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    reranker_model = CrossEncoder(settings.RERANKER_MODEL_NAME)
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    llm = get_llm()
except Exception as e:
    print(f"Lỗi khi khởi tạo các thành phần RAG: {e}")
    embedding_model = None
    reranker_model = None # <-- Thêm
    qdrant_client = None
    llm = None

def build_prompt(query: str, context: list[str]) -> str:
    """
    Xây dựng prompt hoàn chỉnh cho LLM dựa trên template.
    """
    context_str = "\n---\n".join(context)
    
    prompt_template = f"""
Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi của người dùng dựa trên ngữ cảnh được cung cấp dưới đây.
Nếu câu trả lời không có trong ngữ cảnh, hãy nói "Tôi không tìm thấy thông tin trong tài liệu."

Ngữ cảnh:
{context_str}

---
Câu hỏi: {query}

Câu trả lời:
"""
    return prompt_template

def search_qdrant(query: str, document_id: int | None = None, top_k: int = 5) -> list[str]:
    """
    Tìm kiếm các chunks liên quan trong Qdrant.
    """
    if not qdrant_client or not embedding_model:
        return ["Lỗi: Qdrant hoặc Embedding model chưa được khởi tạo."]

    query_vector = embedding_model.encode(query).tolist()

    # Xây dựng bộ lọc (filter) nếu có document_id
    search_filter = None
    if document_id:
        search_filter = {
            "must": [
                {
                    "key": "document_id",
                    "match": {
                        "value": document_id
                    }
                }
            ]
        }

    search_result = qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=search_filter,
        limit=top_k
    )

    # Trích xuất nội dung text từ kết quả
    context = [point.payload['text'] for point in search_result]
    return context

def search_and_rerank(query: str, document_id: int | None = None, top_k: int = 5) -> list[str]:
    """
    Kết hợp tìm kiếm và xếp hạng lại.
    1. Tìm kiếm một lượng lớn hơn các chunks (ví dụ: 20).
    2. Dùng reranker để xếp hạng lại và chọn ra top K tốt nhất.
    """
    if not qdrant_client or not embedding_model or not reranker_model:
        return ["Lỗi: Một trong các thành phần RAG chưa được khởi tạo."]
    
    # 1. Tìm kiếm một lượng lớn hơn, ví dụ gấp 4 lần top_k
    initial_search_limit = top_k * 4
    query_vector = embedding_model.encode(query).tolist()
    
    search_filter = None
    if document_id:
        search_filter = { "must": [{"key": "document_id", "match": {"value": document_id}}] }

    search_result = qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=search_filter,
        limit=initial_search_limit
    )
    
    retrieved_chunks = [point.payload['text'] for point in search_result]

    if not retrieved_chunks:
        return []

    # 2. Rerank các kết quả đã truy xuất
    print(f"Đã truy xuất {len(retrieved_chunks)} chunks. Bắt đầu rerank...")
    # Tạo các cặp [query, chunk] để reranker chấm điểm
    rerank_pairs = [[query, chunk] for chunk in retrieved_chunks]
    # Chấm điểm
    scores = reranker_model.predict(rerank_pairs)
    
    # Kết hợp chunks và điểm số, sau đó sắp xếp
    scored_chunks = list(zip(scores, retrieved_chunks))
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # 3. Chọn ra top K chunks có điểm cao nhất
    final_context = [chunk for score, chunk in scored_chunks[:top_k]]
    
    return final_context

async def get_rag_response_stream(query: str, document_id: int | None = None):
    """
    Thực hiện pipeline RAG hoàn chỉnh và stream câu trả lời.
    """
    if not llm:
        yield "Lỗi: LLM chưa được khởi tạo."
        return

    # 1. Retrieval: Tìm kiếm context
    print(f"Đang tìm kiếm context cho câu hỏi: '{query}'")
    context = search_qdrant(query, document_id)
    print(f"Đã tìm thấy {len(context)} chunks liên quan.")
    
    # 2. Augmentation: Xây dựng prompt
    prompt = build_prompt(query, context)
    
    # 3. Generation: Gọi LLM và stream kết quả
    print("Đang gửi prompt đến LLM và stream câu trả lời...")
    stream = llm.generate_content(prompt, stream=True)
    
    for chunk in stream:
        yield chunk.text