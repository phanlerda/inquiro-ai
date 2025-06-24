# backend/app/core/rag.py

from typing import List, Tuple
import numpy as np
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer, CrossEncoder

from ..config import settings
from .llm import get_llm

# --- KHỞI TẠO CÁC THÀNH PHẦN MỘT LẦN ---
try:
    print("Đang tải các model cho RAG...")
    dense_embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    sparse_embedding_model = SentenceTransformer(settings.SPARSE_VECTOR_MODEL_NAME)
    reranker_model = CrossEncoder(settings.RERANKER_MODEL_NAME)
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    llm = get_llm()
    print("Tải model RAG thành công.")
except Exception as e:
    print(f"Lỗi nghiêm trọng khi khởi tạo các thành phần RAG: {e}")
    dense_embedding_model = None
    sparse_embedding_model = None
    reranker_model = None
    qdrant_client = None
    llm = None

def condense_query_with_history(query: str, history: List[Tuple[str, str]]) -> str:
    """
    Kết hợp câu hỏi mới với lịch sử chat để tạo ra một câu hỏi độc lập.
    """
    if not history:
        return query

    history_str = "\n".join([f"Người dùng: {user_msg}\nTrợ lý: {bot_msg}" for user_msg, bot_msg in history])
    
    prompt = f"""Dựa vào lịch sử trò chuyện dưới đây và câu hỏi mới của người dùng, hãy tạo ra một câu hỏi tìm kiếm độc lập, đầy đủ ngữ cảnh. Câu hỏi này sẽ được dùng để truy vấn cơ sở dữ liệu. Hãy đảm bảo nó bao gồm tất cả các chi tiết liên quan từ lịch sử.

Lịch sử trò chuyện:
{history_str}

Câu hỏi mới: {query}

Câu hỏi độc lập:"""
    
    print("--- Condensing Query ---")
    if not llm:
        print("Lỗi: LLM chưa được khởi tạo, trả về câu hỏi gốc.")
        return query

    response = llm.generate_content(prompt)
    condensed_query = response.text.strip()
    
    print(f"Câu hỏi đã được rút gọn: {condensed_query}")
    print("------------------------")
    
    return condensed_query

def build_prompt(query: str, context: list[str]) -> str:
    """
    Xây dựng prompt hoàn chỉnh cho LLM dựa trên template.
    """
    context_str = "\n---\n".join(context)
    prompt_template = f"""Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi của người dùng một cách chi tiết dựa trên ngữ cảnh được cung cấp dưới đây. Nếu câu trả lời không có trong ngữ cảnh, hãy nói "Tôi không tìm thấy thông tin trong tài liệu."

Ngữ cảnh:
{context_str}

---
Câu hỏi: {query}

Câu trả lời:
"""
    return prompt_template

def search_and_rerank(query: str, document_id: int | None = None, top_k: int = 5) -> list[str]:
    """
    Thực hiện Hybrid Search (dense + sparse) và sau đó rerank kết quả.
    """
    if not all([qdrant_client, dense_embedding_model, sparse_embedding_model, reranker_model]):
        print("Lỗi: Một trong các thành phần RAG (qdrant, models, reranker) chưa được khởi tạo.")
        return []

    # 1. Tạo cả dense và sparse vector cho câu hỏi
    dense_query_vector = dense_embedding_model.encode(query).tolist()
    
    sparse_embedding_raw = sparse_embedding_model.encode(query)
    indices = np.where(sparse_embedding_raw > 0)[0].tolist()
    values = sparse_embedding_raw[indices].tolist()
    sparse_query_vector = models.SparseVector(indices=indices, values=values)

    # 2. Xây dựng các truy vấn con cho tìm kiếm batch
    initial_search_limit = top_k * 5 

    dense_request = models.SearchRequest(
        vector=models.NamedVector(name="dense", vector=dense_query_vector),
        limit=initial_search_limit,
        with_payload=True
    )
    
    sparse_request = models.SearchRequest(
        vector=models.NamedSparseVector(name="text", vector=sparse_query_vector),
        limit=initial_search_limit,
        with_payload=True
    )

    # Thêm bộ lọc nếu có document_id
    search_filter = None
    if document_id:
        search_filter = models.Filter(
            must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))]
        )
        dense_request.filter = search_filter
        sparse_request.filter = search_filter

    # 3. Thực hiện Hybrid Search (Fusion)
    search_results = qdrant_client.search_batch(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        requests=[dense_request, sparse_request]
    )
    
    # 4. Hợp nhất và loại bỏ trùng lặp kết quả
    retrieved_points = {}
    for result_set in search_results:
        for point in result_set:
            retrieved_points[point.id] = point

    if not retrieved_points:
        return []

    # 5. Rerank các kết quả đã được kết hợp
    retrieved_chunks = [point.payload['text'] for point in retrieved_points.values()]
    print(f"Đã truy xuất {len(retrieved_chunks)} chunks từ Hybrid Search. Bắt đầu rerank...")
    rerank_pairs = [[query, chunk] for chunk in retrieved_chunks]
    scores = reranker_model.predict(rerank_pairs)
    
    scored_chunks = list(zip(scores, retrieved_chunks))
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # 6. Trả về top K chunks tốt nhất
    final_context = [chunk for score, chunk in scored_chunks[:top_k]]
    return final_context

async def get_rag_response_stream(query: str, history: List[Tuple[str, str]], document_id: int | None = None):
    """
    Thực hiện pipeline RAG hoàn chỉnh: Condense -> Hybrid Search -> Rerank -> Generate.
    """
    if not llm:
        yield "Lỗi: LLM chưa được khởi tạo."
        return

    standalone_query = condense_query_with_history(query, history)
    
    context = search_and_rerank(standalone_query, document_id)
    
    if not context:
        yield "Xin lỗi, tôi không tìm thấy thông tin nào liên quan trong tài liệu để trả lời câu hỏi của bạn."
        return

    print(f"Đã tìm thấy và xếp hạng lại {len(context)} chunks liên quan nhất.")
    
    # Vẫn dùng câu hỏi gốc của người dùng trong prompt cuối cùng để LLM trả lời đúng trọng tâm
    prompt = build_prompt(query, context)
    
    print("Đang gửi prompt đến LLM và stream câu trả lời...")
    stream = llm.generate_content(prompt, stream=True)
    
    for chunk in stream:
        yield chunk.text