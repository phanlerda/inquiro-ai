# backend/scripts/evaluate.py

# Import các thư viện cần thiết cho async, xử lý đối số dòng lệnh, typing, và dữ liệu
import asyncio
import argparse
from typing import List, Dict
from datasets import Dataset
import pandas as pd
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    ContextRelevance,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import sys
from pathlib import Path

# Thêm đường dẫn để import các module từ app
sys.path.append(str(Path(__file__).parent))

# Import các hàm xử lý RAG và cấu hình
from app.core.rag import _search_and_rerank_documents, build_final_prompt_with_citation
from app.config import settings
from unstructured.partition.pdf import partition_pdf # Import để đọc file PDF

# Cấu hình API key cho LangChain từ biến môi trường
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# --- CÁC HÀM TIỆN ÍCH CHO VIỆC ĐÁNH GIÁ ---
def generate_test_questions(text: str, llm: ChatGoogleGenerativeAI, num_questions: int = 1) -> List[str]:
    """
    Sinh ra các câu hỏi kiểm thử dựa trên nội dung tài liệu sử dụng LLM.
    """
    print(f"Đang tạo {num_questions} câu hỏi kiểm thử...")
    prompt = f"Bạn là một người chuyên tạo câu hỏi. Dựa vào nội dung dưới đây, hãy tạo ra {num_questions} câu hỏi kiểm tra chi tiết và đa dạng. Mỗi câu hỏi trên một dòng.\n\nNội dung:\n---\n{text}\n---\n\n{num_questions} câu hỏi:"
    response = llm.invoke(prompt)
    questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
    questions = [q.split(". ", 1)[1] if ". " in q else q for q in questions]
    print(f"Tạo câu hỏi thành công: {questions}")
    return questions

async def gather_rag_outputs(questions: List[str], document_id: int, llm: ChatGoogleGenerativeAI) -> List[Dict]:
    """
    Chạy pipeline RAG cho từng câu hỏi và thu thập kết quả trả về.
    """
    results = []
    print("Đang thu thập kết quả từ pipeline RAG...")
    for q in questions:
        context_data = _search_and_rerank_documents(query=q, document_id=document_id)
        contexts_text = [doc['text'] for doc in context_data]
        if not contexts_text:
            answer = "Không tìm thấy thông tin."
        else:
            context_for_prompt = "\n\n".join([f"Nguồn [{i+1}]:\n{src['text']}" for i, src in enumerate(context_data)])
            prompt = build_final_prompt_with_citation(q, context_for_prompt)
            response = await llm.ainvoke(prompt)
            answer = response.content
        results.append({"question": q, "answer": answer, "contexts": contexts_text})
    print("Thu thập kết quả thành công.")
    return results

# --- HÀM MAIN ĐỂ CHẠY ĐÁNH GIÁ ---
async def main(filepath: str, document_id: int):
    """
    Hàm chính để thực hiện toàn bộ quy trình đánh giá cho một file cụ thể.
    """
    print(f"--- BẮT ĐẦU ĐÁNH GIÁ CHO FILE: {filepath} (ID: {document_id}) ---")
    
    # --- Khởi tạo các model ---
    print("Đang khởi tạo LLM và Embedding Model cho RAGAs...")
    try:
        gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", convert_system_message_to_human=True)
        ragas_embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    except Exception as e:
        print(f"Lỗi khởi tạo LLM hoặc Embedding: {e}")
        return
    print("Khởi tạo LLM và Embedding Model thành công.")
    
    # --- Bước 1: Đọc nội dung từ file PDF thật ---
    if not Path(filepath).exists():
        print(f"Lỗi: Không tìm thấy file tại đường dẫn '{filepath}'")
        return
        
    print(f"Đang đọc nội dung từ file: {filepath}")
    elements = partition_pdf(filename=filepath, strategy="fast")
    document_text = "\n\n".join([str(el) for el in elements])

    if not document_text.strip():
        print("Lỗi: Không thể trích xuất nội dung từ file PDF.")
        return

    # --- Bước 2: Tạo câu hỏi từ nội dung thật ---
    # Giảm số lượng câu hỏi để tránh lỗi rate limit
    test_questions = generate_test_questions(document_text, llm=gemini_llm, num_questions=1)
    if not test_questions:
        print("Không thể tạo câu hỏi từ nội dung file. Dừng lại.")
        return

    # --- Bước 3: Chạy pipeline RAG để thu thập kết quả ---
    rag_outputs = await gather_rag_outputs(test_questions, document_id=document_id, llm=gemini_llm)
    rag_dataset = Dataset.from_list(rag_outputs)

    # --- Bước 4: Đánh giá bằng RAGAs ---
    print("Bắt đầu đánh giá với RAGAs...")
    metrics = [faithfulness, answer_relevancy, ContextRelevance()]
    
    result = evaluate(
        dataset=rag_dataset,
        metrics=metrics,
        llm=gemini_llm,
        embeddings=ragas_embeddings,
    )

    # --- Bước 5: In kết quả ---
    print("\n--- KẾT QUẢ ĐÁNH GIÁ ---")
    df = result.to_pandas()
    print(df.to_string())
    print("-------------------------")
    print("\nĐiểm số trung bình:")
    print(df.mean(numeric_only=True))

if __name__ == "__main__":
    # Sử dụng argparse để nhận tham số từ dòng lệnh
    parser = argparse.ArgumentParser(description="Chạy đánh giá RAGAs cho một tài liệu cụ thể.")
    parser.add_argument("--file", type=str, required=True, help="Đường dẫn đến file PDF cần đánh giá (ví dụ: storage/chimera.pdf).")
    parser.add_argument("--id", type=int, required=True, help="ID của tài liệu trong database.")
    
    args = parser.parse_args()
    
    # Chạy hàm main bằng asyncio với các tham số từ dòng lệnh
    asyncio.run(main(filepath=args.file, document_id=args.id))