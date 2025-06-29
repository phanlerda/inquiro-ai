// frontend/src/app/page.tsx
'use client';

import Sidebar from '@/components/chat/Sidebar';
import ChatArea from '@/components/chat/ChatArea';
import { useEffect, useState, Dispatch, SetStateAction } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { Document, Message } from '@/types/chat';

// Định nghĩa kiểu cho state conversations
export type Conversations = { [docId: number]: Message[] };

export default function ChatPage() {
  const { token } = useAuthStore();
  const router = useRouter();
  
  // State quản lý TẤT CẢ các cuộc trò chuyện
  const [conversations, setConversations] = useState<Conversations>({});
  
  // State quản lý tài liệu NÀO đang được chọn
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  
  const [isAuthChecked, setIsAuthChecked] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      setIsAuthChecked(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Hàm được truyền xuống Sidebar để xử lý khi người dùng chọn một tài liệu
  const handleSelectDocument = (doc: Document) => {
    setSelectedDocument(doc);
  };
  
  // Hàm được truyền xuống Sidebar để xử lý khi người dùng muốn bắt đầu chat mới
  const handleNewChat = () => {
    // Nếu có tài liệu đang được chọn, chỉ xóa lịch sử chat của tài liệu đó
    if (selectedDocument) {
      setConversations(prev => {
        const newConversations = { ...prev };
        delete newConversations[selectedDocument.id]; // Xóa cuộc trò chuyện của doc này
        return newConversations;
      });
    }
    // Dù có hay không, bỏ chọn tài liệu để hiển thị màn hình chào mừng
    setSelectedDocument(null);
  };

  if (!isAuthChecked) {
    return (
        <div className="flex h-screen w-full items-center justify-center bg-gray-100">
            <p className="animate-pulse">Đang tải và xác thực...</p>
        </div>
    );
  }

  // Lấy ra mảng messages cho document đang được chọn
  const currentMessages = selectedDocument ? conversations[selectedDocument.id] || [] : [];

  return (
    <div className="flex h-screen bg-gray-100 antialiased text-gray-800">
      <Sidebar 
        onSelectDocument={handleSelectDocument}
        onNewChat={handleNewChat}
        selectedDocumentId={selectedDocument?.id || null}
      />
      <ChatArea 
        document={selectedDocument} 
        messages={currentMessages}
        setConversations={setConversations} // Truyền hàm set state xuống
      />
    </div>
  );
}