# backend/app/core/rag.py

from typing import List, Tuple, Dict
import numpy as np
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import ScoredPoint
from sentence_transformers import SentenceTransformer, CrossEncoder
from tavily import TavilyClient

from ..config import settings
from .llm import get_llm
from ..schemas.chat import Source

# --- KHỞI TẠO CÁC THÀNH PHẦN MỘT LẦN ---
try:
    print("Đang tải các model cho RAG...")
    dense_embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    sparse_embedding_model = SentenceTransformer(settings.SPARSE_VECTOR_MODEL_NAME)
    reranker_model = CrossEncoder(settings.RERANKER_MODEL_NAME)
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    llm = get_llm() # get_llm() bây giờ trả về một object của LangChain
    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    print("Tải model RAG và các client thành công.")
except Exception as e:
    print(f"Lỗi nghiêm trọng khi khởi tạo các thành phần RAG: {e}")
    dense_embedding_model = None
    sparse_embedding_model = None
    reranker_model = None
    qdrant_client = None
    llm = None
    tavily_client = None

# ==============================================================================
# ĐỊNH NGHĨA CÁC CÔNG CỤ (TOOLS)
# ==============================================================================

def document_search_tool(query: str, document_id: int | None = None) -> Dict:
    """
    Công cụ tìm kiếm thông tin trong các tài liệu đã được upload.
    """
    print(f"--- Đang sử dụng Document Search Tool cho câu hỏi: '{query}' ---")
    context_data = _search_and_rerank_documents(query, document_id, top_k=5)
    
    if not context_data:
        return {"context": "Không tìm thấy thông tin liên quan trong tài liệu.", "sources": []}
        
    context_text = "\n---\n".join([doc['text'] for doc in context_data])
    sources = [Source(**doc) for doc in context_data]
    
    return {"context": context_text, "sources": sources}

def web_search_tool(query: str) -> Dict:
    """
    Công cụ tìm kiếm thông tin trên internet sử dụng Tavily.
    """
    print(f"--- Đang sử dụng Web Search Tool cho câu hỏi: '{query}' ---")
    if not tavily_client:
        return {"context": "Lỗi: Tavily client chưa được khởi tạo.", "sources": []}
        
    try:
        response = tavily_client.search(query=query, search_depth="advanced", max_results=5)
        context = "\n---\n".join([obj["content"] for obj in response['results']])
        sources = [
            Source(document_id=0, filename=obj['url'], text=obj['content']) 
            for obj in response['results']
        ]
        return {"context": context, "sources": sources}
    except Exception as e:
        print(f"Lỗi khi tìm kiếm trên web: {e}")
        return {"context": "Không thể thực hiện tìm kiếm trên web vào lúc này.", "sources": []}

# ==============================================================================
# CÁC HÀM HỖ TRỢ
# ==============================================================================

def _search_and_rerank_documents(query: str, document_id: int | None = None, top_k: int = 5) -> List[Dict]:
    # (Hàm này không thay đổi vì không gọi LLM)
    # ... giữ nguyên nội dung hàm ...
    if not all([qdrant_client, dense_embedding_model, sparse_embedding_model, reranker_model]):
        print("Lỗi: Một trong các thành phần RAG chưa được khởi tạo.")
        return []
    dense_query_vector = dense_embedding_model.encode(query).tolist()
    sparse_embedding_raw = sparse_embedding_model.encode(query)
    indices = np.where(sparse_embedding_raw > 0)[0].tolist()
    values = sparse_embedding_raw[indices].tolist()
    sparse_query_vector = models.SparseVector(indices=indices, values=values)
    initial_search_limit = top_k * 5
    dense_request = models.SearchRequest(vector=models.NamedVector(name="dense", vector=dense_query_vector), limit=initial_search_limit, with_payload=True)
    sparse_request = models.SearchRequest(vector=models.NamedSparseVector(name="text", vector=sparse_query_vector), limit=initial_search_limit, with_payload=True)
    if document_id:
        search_filter = models.Filter(must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))])
        dense_request.filter = search_filter
        sparse_request.filter = search_filter
    search_results = qdrant_client.search_batch(collection_name=settings.QDRANT_COLLECTION_NAME, requests=[dense_request, sparse_request])
    retrieved_points: Dict[str, ScoredPoint] = {}
    for result_set in search_results:
        for point in result_set:
            retrieved_points[point.id] = point
    if not retrieved_points:
        return []
    retrieved_chunks = [point.payload['text'] for point in retrieved_points.values()]
    rerank_pairs = [[query, chunk] for chunk in retrieved_chunks]
    scores = reranker_model.predict(rerank_pairs)
    points_list = list(retrieved_points.values())
    scored_points = list(zip(scores, points_list))
    scored_points.sort(key=lambda x: x[0], reverse=True)
    final_context_data = []
    for score, point in scored_points[:top_k]:
        final_context_data.append({
            "text": point.payload['text'],
            "document_id": point.payload['document_id'],
            "filename": point.payload['filename']
        })
    return final_context_data

def condense_query_with_history(query: str, history: List[Tuple[str, str]]) -> str:
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

    # THAY ĐỔI Ở ĐÂY: Dùng .invoke() và .content
    response = llm.invoke(prompt)
    condensed_query = response.content.strip()
    
    print(f"Câu hỏi đã được rút gọn: {condensed_query}")
    print("------------------------")
    return condensed_query

def build_final_prompt_with_citation(query: str, context: str) -> str:
    prompt_template = f"""Bạn là một trợ lý AI xuất sắc. Hãy trả lời câu hỏi của người dùng dựa trên các nguồn thông tin được cung cấp dưới đây. Khi trả lời, bạn BẮT BUỘC phải trích dẫn các nguồn bạn đã sử dụng bằng cách thêm `[Nguồn x]` vào cuối mỗi câu hoặc mệnh đề có thông tin từ nguồn đó. Ví dụ: "Helios-V là một dự án nghiên cứu về năng lượng mặt trời [Nguồn 1]." Nếu thông tin không có trong các nguồn được cung cấp, hãy trả lời "Tôi không tìm thấy thông tin trong tài liệu."

Các nguồn (Mỗi nguồn được đánh số, ví dụ [Nguồn 1], [Nguồn 2],...):
{context}

---
Câu hỏi: {query}

Câu trả lời (nhớ trích dẫn nguồn):
"""
    return prompt_template

# ==============================================================================
# LOGIC AGENT CHÍNH
# ==============================================================================

async def get_agentic_rag_response(query: str, history: List[Tuple[str, str]], document_id: int | None = None) -> Dict:
    if not llm:
        return {"answer": "Lỗi: LLM chưa được khởi tạo.", "sources": []}

    standalone_query = condense_query_with_history(query, history)

    tool_selection_prompt = f"""Bạn là một Agent định tuyến thông minh. Dựa trên câu hỏi của người dùng, hãy quyết định công cụ nào là phù hợp nhất để trả lời.
Bạn chỉ có thể chọn một trong hai công cụ sau:
1. `document_search`: Dùng để tìm kiếm trong các tài liệu nội bộ, trả lời các câu hỏi về các dự án cụ thể đã biết, các báo cáo, các file đã được upload.
2. `web_search`: Dùng để tìm kiếm trên internet, trả lời các câu hỏi kiến thức chung, tin tức, sự kiện thời sự, hoặc các chủ đề không có trong tài liệu nội bộ.

Câu hỏi của người dùng: "{standalone_query}"

Hãy trả lời bằng MỘT TỪ DUY NHẤT: `document_search` hoặc `web_search`."""

    print("--- Agent đang lựa chọn công cụ ---")
    # THAY ĐỔI Ở ĐÂY: Dùng .ainvoke() và .content
    tool_choice_response = await llm.ainvoke(tool_selection_prompt)
    chosen_tool = tool_choice_response.content.strip().lower()
    print(f"Agent đã chọn: {chosen_tool}")

    if "document_search" in chosen_tool:
        tool_result = document_search_tool(standalone_query, document_id)
    elif "web_search" in chosen_tool:
        tool_result = web_search_tool(standalone_query)
    else:
        print("Lựa chọn không rõ ràng, mặc định dùng document_search.")
        tool_result = document_search_tool(standalone_query, document_id)

    context = tool_result["context"]
    sources = tool_result["sources"]

    if not context or "Không tìm thấy" in context:
        return {"answer": context, "sources": sources}

    context_for_prompt = "\n\n".join([f"Nguồn [{i+1}]:\n{src.text}" for i, src in enumerate(sources)])
    final_prompt = build_final_prompt_with_citation(query, context_for_prompt)
    
    print("Đang gửi prompt cuối cùng đến LLM...")
    # THAY ĐỔI Ở ĐÂY: Dùng .ainvoke() và .content
    final_response = await llm.ainvoke(final_prompt)

    return {"answer": final_response.content, "sources": sources}