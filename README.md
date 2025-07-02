# 🤖 Inquiro AI

Đây là một dự án chatbot RAG (Retrieval-Augmented Generation) fullstack, được xây dựng với mục tiêu cung cấp một nền tảng mạnh mẽ, có khả năng mở rộng để trò chuyện với các tài liệu cá nhân và kiến thức từ web.

## 📸 Demo giao diện

Dưới đây là một số ảnh minh họa các tính năng chính của hệ thống:

- **Màn hình đăng nhập:**
  ![Login](./frontend/public/login-demo.png)

- **Giao diện chat với prompt và câu trả lời:**
  ![Prompt & Answer](./frontend/public/prompt-answer-demo.png)

- **Hiển thị nguồn trích dẫn:**
  ![Nguồn trích dẫn](./frontend/public/source-demo.png)

## ✨ Các tính năng nổi bật

*   **Kiến trúc:** Backend xây dựng bằng **FastAPI (Python)**, Frontend bằng **Next.js & Tailwind CSS (TypeScript)**.
*   **Pipeline RAG:**
    *   **Hybrid Search:** Kết hợp tìm kiếm ngữ nghĩa (Dense Vector) và tìm kiếm từ khóa (Sparse Vector) để có độ chính xác cao nhất.
    *   **Reranking:** Sử dụng Cross-Encoder để xếp hạng lại các kết quả, đảm bảo context đưa vào LLM là phù hợp nhất.
    *   **Xử lý Hội thoại:** Hiểu các câu hỏi nối tiếp bằng kỹ thuật Query Condensing.
*   **Agentic RAG:** Chatbot có khả năng tự quyết định sử dụng công cụ phù hợp (tìm kiếm trong tài liệu hoặc tìm kiếm trên web) để trả lời câu hỏi.
*   **Trích dẫn Nguồn (Citation):** Câu trả lời của chatbot có trích dẫn nguồn gốc thông tin, tăng độ tin cậy.
*   **Hệ thống Đa người dùng:** Hỗ trợ đăng ký, đăng nhập với xác thực JWT, đảm bảo dữ liệu của mỗi người dùng được bảo mật.
*   **Xử lý Tài liệu Thông minh:** Sử dụng thư viện `unstructured` để phân tích và trích xuất nội dung từ các file PDF phức tạp.
*   **Môi trường Đóng gói:** Toàn bộ các dịch vụ (PostgreSQL, Qdrant) được quản lý qua **Docker**, dễ dàng cài đặt và triển khai.
*   **Đánh giá Hệ thống:** Cung cấp script để đánh giá chất lượng pipeline RAG một cách khách quan bằng framework **RAGAs**.

## 🚀 Stack Công nghệ

*   **Backend:**
    *   **Framework:** FastAPI, Pydantic
    *   **Database:** PostgreSQL (metadata), Qdrant (vector store)
    *   **LLM & Embedding:** Google Gemini, Sentence-Transformers (cho dense & sparse vectors)
    *   **Xử lý tài liệu:** `unstructured`, `PyMuPDF`
    *   **Xác thực:** JWT (python-jose), Passlib
    *   **Quản lý phụ thuộc:** Poetry
*   **Frontend:**
    *   **Framework:** Next.js (App Router), React, TypeScript
    *   **Styling:** Tailwind CSS
    *   **Quản lý State:** Zustand
    *   **Gọi API:** Axios
*   **Infrastructure:**
    *   **Containerization:** Docker, Docker Compose

## 🔧 Cài đặt và Chạy dự án

### Yêu cầu tiên quyết

*   **Docker** và **Docker Compose** đã được cài đặt.
*   **Poetry** (trình quản lý gói của Python) đã được cài đặt.
*   **Node.js** và **npm** (hoặc `yarn`) đã được cài đặt.
*   **API Keys:**
    *   Google Gemini API Key
    *   Tavily AI API Key (cho chức năng web search)

### Bước 1: Clone dự án

```bash
git clone https://github.com/phanlerda/inquiro-ai.git
```

### Bước 2: Cấu hình Backend

1.  **Di chuyển vào thư mục backend:**
    ```bash
    cd backend
    ```

2.  **Tạo file biến môi trường:**
    Tạo một file `.env` từ file mẫu `.env.example` hoặc tạo mới với nội dung sau:
    ```env
    # backend/.env

    # API Keys
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"

    # Database
    DATABASE_URL="postgresql://rag_user:rag_password@localhost:5432/rag_db"

    # Vector DB
    QDRANT_URL="http://localhost:6333"
    QDRANT_COLLECTION_NAME="rag_documents"

    # Models
    EMBEDDING_MODEL_NAME="BAAI/bge-small-en-v1.5"
    SPARSE_VECTOR_MODEL_NAME="naver/splade-cocondenser-ensembledistil"
    RERANKER_MODEL_NAME="BAAI/bge-reranker-base"

    # JWT
    SECRET_KEY="<RUN_`openssl rand -hex 32`_TO_GENERATE_A_SECRET_KEY>"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    ```
    **Quan trọng:** Thay thế các giá trị `YOUR_..._KEY` và tạo một `SECRET_KEY` ngẫu nhiên.

3.  **Khởi động các dịch vụ Backend (Database & Vector DB):**
    ```bash
    docker-compose up -d
    ```

4.  **Cài đặt các phụ thuộc Python:**
    ```bash
    poetry install
    ```

5.  **Cài đặt các dependencies hệ thống (cho WSL/Linux):**
    Thư viện `unstructured` yêu cầu các công cụ sau:
    ```bash
    sudo apt-get update
    sudo apt-get install -y poppler-utils tesseract-ocr
    ```

6.  **Chạy server Backend:**
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
    Backend API sẽ chạy tại `http://localhost:8000`. Bạn có thể truy cập `http://localhost:8000/docs` để xem tài liệu API.

### Bước 3: Cấu hình Frontend

1.  **Mở một terminal mới** và di chuyển vào thư mục `frontend`:
    ```bash
    cd frontend
    ```

2.  **Tạo file biến môi trường:**
    Tạo file `.env.local` với nội dung:
    ```env
    # frontend/.env.local
    NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ```

3.  **Cài đặt các phụ thuộc Node.js:**
    ```bash
    npm install
    ```

4.  **Chạy server Frontend:**
    ```bash
    npm run dev
    ```
    Frontend sẽ chạy tại `http://localhost:3000`.

### Bước 4: Sử dụng Ứng dụng

1.  Mở trình duyệt và truy cập `http://localhost:3000`.
2.  Bạn sẽ được chuyển hướng đến trang đăng ký. Hãy tạo một tài khoản.
3.  Đăng nhập bằng tài khoản vừa tạo.
4.  Upload một tài liệu PDF.
5.  Chọn tài liệu từ sidebar và bắt đầu trò chuyện!

## 🧪 Đánh giá Hệ thống (Tùy chọn)

Dự án cung cấp một script để đánh giá chất lượng pipeline RAG bằng `RAGAs`.

1.  Đảm bảo server backend đang chạy.
2.  Mở một terminal mới trong thư mục `backend`.
3.  Chạy lệnh sau, thay thế `--file` và `--id` bằng thông tin tài liệu bạn muốn đánh giá:
    ```bash
    poetry run python evaluate.py --file storage/<ten_file_pdf> --id <id_cua_tai_lieu>
    ```
    Ví dụ: `poetry run python evaluate.py --file storage/my_doc.pdf --id 1`


## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo một Pull Request hoặc mở một Issue để thảo luận về các thay đổi bạn muốn thực hiện.

## 📄 Giấy phép

Dự án này được cấp phép theo Giấy phép MIT.