// frontend/src/types/chat.ts
export interface Source {
  document_id: number;
  filename: string;
  text: string;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  sources?: Source[];
  responseTo?: string; // ID của tin nhắn mà tin nhắn này đang trả lời
}

export interface Document {
  id: number;
  filename: string;
  status: 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
}