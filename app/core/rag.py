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
SYSTEM_ADMIN_USER_ID = 1 # Thay đổi giá trị này nếu ID admin của bạn khác

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
    # ... (Hàm này giữ nguyên như trước)
    print(f"--- Web Search Tool: query='{query}' ---")
    if not tavily_client: return {"context": "Lỗi: Tavily client chưa được khởi tạo.", "sources": []}
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
    - Nếu document_id được cung cấp: tìm trong document đó (nếu user có quyền hoặc là doc hệ thống).
    - Nếu không: tìm trên tài liệu của user VÀ tài liệu hệ thống (nếu user_id được cung cấp).
    - Nếu không có user_id và không có document_id: chỉ tìm trên tài liệu hệ thống.
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

    # Xây dựng bộ lọc Qdrant
    filter_must_conditions = []
    filter_should_conditions = []

    if document_id:
        # Ưu tiên tìm kiếm trong một document cụ thể
        filter_must_conditions.append(
            models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))
        )
        if user_id:
            # Người dùng đã đăng nhập và chỉ định document_id
            # Tài liệu này phải thuộc sở hữu của họ HOẶC là tài liệu hệ thống
            filter_should_conditions.extend([
                models.FieldCondition(key="owner_id", match=models.MatchValue(value=user_id)),
                models.FieldCondition(key="owner_id", match=models.MatchValue(value=SYSTEM_ADMIN_USER_ID))
            ])
        else: # Khách vãng lai chỉ định document_id (phải là tài liệu hệ thống)
            filter_must_conditions.append(
                models.FieldCondition(key="owner_id", match=models.MatchValue(value=SYSTEM_ADMIN_USER_ID))
            )
    elif user_id:
        # Người dùng đã đăng nhập, không chỉ định document_id cụ thể
        # Tìm trong tài liệu của họ VÀ tài liệu hệ thống
        filter_should_conditions.extend([
            models.FieldCondition(key="owner_id", match=models.MatchValue(value=user_id)),
            models.FieldCondition(key="owner_id", match=models.MatchValue(value=SYSTEM_ADMIN_USER_ID))
        ])
    else:
        # Khách vãng lai, không chỉ định document_id
        # Chỉ tìm trong tài liệu hệ thống
        filter_must_conditions.append(
            models.FieldCondition(key="owner_id", match=models.MatchValue(value=SYSTEM_ADMIN_USER_ID))
        )

    final_filter = None
    if filter_must_conditions and filter_should_conditions:
        final_filter = models.Filter(must=filter_must_conditions, should=filter_should_conditions)
    elif filter_must_conditions:
        final_filter = models.Filter(must=filter_must_conditions)
    elif filter_should_conditions:
        final_filter = models.Filter(should=filter_should_conditions)
    
    if final_filter:
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
    # (Hàm này giữ nguyên)
    if not history: return query
    history_str = "\n".join([f"Người dùng: {user_msg}\nTrợ lý: {bot_msg}" for user_msg, bot_msg in history])
    prompt = f"Dựa vào lịch sử trò chuyện...\nCâu hỏi độc lập:" # (Giữ nguyên prompt)
    print("--- Condensing Query ---")
    if not llm: return query
    response = llm.invoke(prompt)
    condensed_query = response.content.strip()
    print(f"Câu hỏi đã được rút gọn: {condensed_query}")
    print("------------------------")
    return condensed_query

def build_final_prompt_with_citation(query: str, context: str) -> str:
    # (Hàm này giữ nguyên)
    prompt_template = f"Bạn là một trợ lý AI xuất sắc...\nCác nguồn:\n{context}\n---\nCâu hỏi: {query}\nCâu trả lời (nhớ trích dẫn nguồn):"
    return prompt_template

def delete_vectors_for_document(document_id: int):
    """
    Xóa tất cả các vector trong Qdrant thuộc về một document_id cụ thể.
    """
    if not qdrant_client:
        print("Lỗi: Qdrant client chưa được khởi tạo. Bỏ qua việc xóa vector.")
        return

    print(f"Đang xóa các vector cho document_id: {document_id}")
    try:
        qdrant_client.delete(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
            wait=True
        )
        print(f"Xóa thành công các vector cho document_id: {document_id}")
    except Exception as e:
        print(f"Lỗi khi xóa vector từ Qdrant cho document_id {document_id}: {e}")
        # Có thể raise lỗi ở đây để transaction của DB được rollback nếu cần
        
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
        # Nếu người dùng đã chỉ định một tài liệu, ưu tiên tìm trong đó, không cần hỏi LLM
        print(f"Ưu tiên tìm kiếm trong document_id: {document_id} do người dùng chỉ định.")
        chosen_tool_name = "document_search"
    else:
        # Nếu không, để LLM quyết định
        tool_selection_prompt = f"""Bạn là một Agent định tuyến thông minh. Dựa trên câu hỏi của người dùng, hãy quyết định công cụ nào là phù hợp nhất để trả lời.
Bạn chỉ có thể chọn một trong hai công cụ sau:
1. `document_search`: Dùng khi câu hỏi có khả năng được trả lời từ các tài liệu nội bộ đã được cung cấp.
2. `web_search`: Dùng khi câu hỏi mang tính kiến thức chung, tin tức cập nhật, hoặc khi bạn nghĩ rằng tài liệu nội bộ không chứa câu trả lời.

Câu hỏi của người dùng: "{standalone_query}"

Hãy trả lời bằng MỘT TỪ DUY NHẤT: `document_search` hoặc `web_search`."""

        print("--- Agent đang lựa chọn công cụ ---")
        tool_choice_response = await llm.ainvoke(tool_selection_prompt)
        chosen_tool_name = tool_choice_response.content.strip().lower()
        print(f"Agent đã chọn: {chosen_tool_name}")

    tool_result = {"context": "Không thể xác định công cụ phù hợp hoặc thực thi công cụ.", "sources": []}
    if "document_search" in chosen_tool_name:
        tool_result = document_search_tool(standalone_query, document_id, user_id)
    elif "web_search" in chosen_tool_name:
        # Chỉ tìm web nếu không có document_id cụ thể được yêu cầu bởi người dùng
        if document_id:
            print("Người dùng yêu cầu document cụ thể, không thực hiện web search. Sẽ thử tìm trong document.")
            tool_result = document_search_tool(standalone_query, document_id, user_id)
        else:
            tool_result = web_search_tool(standalone_query)
    else:
        print("Lựa chọn không rõ ràng từ LLM, mặc định dùng document_search.")
        tool_result = document_search_tool(standalone_query, document_id, user_id)

    context_from_tool = tool_result["context"]
    sources_from_tool = tool_result["sources"]

    if not context_from_tool or "Không tìm thấy" in context_from_tool or not sources_from_tool:
        # Nếu công cụ không trả về context hoặc source có ý nghĩa
        # (ví dụ: "Không tìm thấy thông tin...")
        # thì trả về luôn thông báo đó, không cần gọi LLM nữa.
        return {"answer": context_from_tool, "sources": sources_from_tool}

    # Đảm bảo sources_from_tool là một list các đối tượng Source
    if not all(isinstance(src, Source) for src in sources_from_tool):
        print(f"Cảnh báo: sources_from_tool không phải là list các object Source. Giá trị: {sources_from_tool}")
        try:
            sources_from_tool = [Source(**src_dict) if isinstance(src_dict, dict) else src for src_dict in sources_from_tool]
            sources_from_tool = [src for src in sources_from_tool if isinstance(src, Source)]
        except Exception:
            sources_from_tool = [] # Nếu không chuyển đổi được, trả về list rỗng

    # Chỉ xây dựng context_for_prompt nếu có sources hợp lệ
    if sources_from_tool:
        context_for_prompt = "\n\n".join([f"Nguồn [{i+1}]:\n{src.text}" for i, src in enumerate(sources_from_tool)])
        final_prompt = build_final_prompt_with_citation(query, context_for_prompt) # Vẫn dùng câu hỏi gốc
    else: # Trường hợp hiếm: có context_from_tool nhưng không có sources_from_tool
        final_prompt = build_final_prompt_with_citation(query, context_from_tool)


    print("Đang gửi prompt cuối cùng đến LLM...")
    final_response = await llm.ainvoke(final_prompt)

    return {"answer": final_response.content, "sources": sources_from_tool}