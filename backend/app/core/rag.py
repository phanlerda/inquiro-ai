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
    llm = get_llm()
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

# ID của người dùng hệ thống/admin
SYSTEM_ADMIN_USER_ID = 1

# ==============================================================================
# ĐỊNH NGHĨA CÁC CÔNG CỤ (TOOLS)
# ==============================================================================

def document_search_tool(query: str, document_id: int | None = None, user_id: int | None = None) -> Dict:
    """
    Công cụ tìm kiếm thông tin trong tài liệu.
    """
    print(f"--- Document Search Tool: query='{query}', doc_id={document_id}, user_id={user_id} ---")
    context_data = _search_and_rerank_documents(query, document_id, user_id, top_k=5)
    
    if not context_data:
        return {"context": "Không tìm thấy thông tin liên quan trong các tài liệu được phép truy cập.", "sources": []}
        
    context_text = "\n---\n".join([doc['text'] for doc in context_data])
    sources = [Source(**doc) for doc in context_data]
    
    return {"context": context_text, "sources": sources}

def web_search_tool(query: str) -> Dict:
    """
    Công cụ tìm kiếm thông tin trên internet sử dụng Tavily.
    """
    print(f"--- Web Search Tool: query='{query}' ---")
    if not tavily_client: 
        return {"context": "Lỗi: Tavily client chưa được khởi tạo.", "sources": []}
    try:
        response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
        if not response or 'results' not in response or not response['results']:
            return {"context": "Không tìm thấy kết quả nào trên web cho câu hỏi này.", "sources": []}
        context = "\n---\n".join([obj["content"] for obj in response['results']])
        sources = [Source(document_id=0, filename=obj.get('url', 'Web Search'), text=obj['content']) for obj in response['results']]
        return {"context": context, "sources": sources}
    except Exception as e:
        print(f"Lỗi khi tìm kiếm trên web: {e}")
        return {"context": "Không thể thực hiện tìm kiếm trên web vào lúc này.", "sources": []}

# ==============================================================================
# CÁC HÀM HỖ TRỢ
# ==============================================================================

def _search_and_rerank_documents(
    query: str, document_id: int | None = None, user_id: int | None = None, top_k: int = 5
) -> List[Dict]:
    """
    Hàm nội bộ để thực hiện Hybrid Search và Rerank.
    """
    if not all([qdrant_client, dense_embedding_model, sparse_embedding_model, reranker_model]):
        print("Lỗi: Một trong các thành phần RAG (qdrant, models, reranker) chưa được khởi tạo.")
        return []

    dense_query_vector = dense_embedding_model.encode(query).tolist()
    sparse_embedding_raw = sparse_embedding_model.encode(query)
    sparse_indices = np.where(sparse_embedding_raw > 0)[0].tolist()
    sparse_values = sparse_embedding_raw[sparse_indices].tolist()
    sparse_query_vector = models.SparseVector(indices=sparse_indices, values=sparse_values)

    initial_search_limit = top_k * 5
    dense_request = models.SearchRequest(vector=models.NamedVector(name="dense", vector=dense_query_vector), limit=initial_search_limit, with_payload=True)
    sparse_request = models.SearchRequest(vector=models.NamedSparseVector(name="text", vector=sparse_query_vector), limit=initial_search_limit, with_payload=True)

    filter_must_conditions = []
    if user_id:
        filter_must_conditions.append(
            models.FieldCondition(key="owner_id", match=models.MatchValue(value=user_id))
        )
    else: # Khách vãng lai chỉ được truy cập tài liệu hệ thống
        filter_must_conditions.append(
            models.FieldCondition(key="owner_id", match=models.MatchValue(value=SYSTEM_ADMIN_USER_ID))
        )

    if document_id:
        filter_must_conditions.append(
            models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))
        )

    final_filter = models.Filter(must=filter_must_conditions)
    dense_request.filter = final_filter
    sparse_request.filter = final_filter
    print(f"Áp dụng bộ lọc Qdrant: {final_filter.json(exclude_none=True)}")

    search_results = qdrant_client.search_batch(collection_name=settings.QDRANT_COLLECTION_NAME, requests=[dense_request, sparse_request])
    
    retrieved_points: Dict[str, ScoredPoint] = {}
    for result_set in search_results:
        for point in result_set:
            retrieved_points[point.id] = point

    if not retrieved_points:
        return []

    rerank_pairs = [[query, point.payload['text']] for point in retrieved_points.values()]
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
        return query
    response = llm.invoke(prompt)
    condensed_query = response.content.strip()
    print(f"Câu hỏi đã được rút gọn: {condensed_query}")
    print("------------------------")
    return condensed_query

def build_final_prompt(query: str, context: str) -> str:
    """
    Xây dựng prompt cuối cùng để tạo câu trả lời.
    Prompt này chỉ yêu cầu LLM trả lời dựa trên context, không yêu cầu trích dẫn.
    """
    prompt_template = f"""Bạn là một trợ lý AI xuất sắc, chuyên trả lời câu hỏi của người dùng một cách chi tiết, mạch lạc và hữu ích dựa trên các thông tin trong phần "Ngữ cảnh" được cung cấp.
Hãy đọc kỹ ngữ cảnh và sử dụng nó để đưa ra câu trả lời tốt nhất cho câu hỏi của người dùng.
Nếu thông tin cần thiết không có trong ngữ cảnh, hãy lịch sự thông báo rằng bạn không tìm thấy thông tin trong tài liệu được cung cấp.

---
Ngữ cảnh:
{context}
---
Câu hỏi: {query}

Câu trả lời chi tiết:
"""
    return prompt_template

def delete_vectors_for_document(document_id: int):
    if not qdrant_client:
        print("Lỗi: Qdrant client chưa được khởi tạo. Bỏ qua việc xóa vector.")
        return
    print(f"Đang xóa các vector cho document_id: {document_id}")
    try:
        qdrant_client.delete(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))]
                )
            ),
            wait=True
        )
        print(f"Xóa thành công các vector cho document_id: {document_id}")
    except Exception as e:
        print(f"Lỗi khi xóa vector từ Qdrant cho document_id {document_id}: {e}")
        
# ==============================================================================
# LOGIC AGENT CHÍNH
# ==============================================================================

async def get_agentic_rag_response(
    query: str, history: List[Tuple[str, str]], document_id: int | None = None, user_id: int | None = None
) -> Dict:
    if not llm:
        return {"answer": "Lỗi: LLM chưa được khởi tạo.", "sources": []}

    standalone_query = condense_query_with_history(query, history)

    chosen_tool_name = ""
    if document_id:
        print(f"Ưu tiên tìm kiếm trong document_id: {document_id} do người dùng chỉ định.")
        chosen_tool_name = "document_search"
    else:
        tool_selection_prompt = f"""Bạn là một Agent định tuyến thông minh...
Câu hỏi của người dùng: "{standalone_query}"
Hãy trả lời bằng MỘT TỪ DUY NHẤT: `document_search` hoặc `web_search`."""
        print("--- Agent đang lựa chọn công cụ ---")
        tool_choice_response = await llm.ainvoke(tool_selection_prompt)
        chosen_tool_name = tool_choice_response.content.strip().lower()
        print(f"Agent đã chọn: {chosen_tool_name}")

    if "document_search" in chosen_tool_name:
        tool_result = document_search_tool(standalone_query, document_id, user_id)
    elif "web_search" in chosen_tool_name:
        tool_result = web_search_tool(standalone_query)
    else:
        print("Lựa chọn không rõ ràng từ LLM, mặc định dùng document_search.")
        tool_result = document_search_tool(standalone_query, document_id, user_id)

    context_from_tool = tool_result["context"]
    sources_from_tool = tool_result["sources"]

    if not context_from_tool or "Không tìm thấy" in context_from_tool:
        return {"answer": context_from_tool, "sources": sources_from_tool}

    # Chúng ta vẫn gửi context được đánh số để LLM dễ theo dõi, nhưng không yêu cầu nó trích dẫn
    context_for_prompt = "\n\n".join([f"Thông tin nguồn {i+1}:\n{src.text}" for i, src in enumerate(sources_from_tool)])
    final_prompt = build_final_prompt(query, context_for_prompt)

    print("Đang gửi prompt cuối cùng đến LLM...")
    final_response = await llm.ainvoke(final_prompt)

    return {"answer": final_response.content, "sources": sources_from_tool}