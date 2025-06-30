'use client';

import Sidebar from '@/components/chat/Sidebar';
import ChatArea from '@/components/chat/ChatArea';
import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { Document, Message } from '@/types/chat';

export type Conversations = { [docId: number]: Message[] };

export default function ChatPage() {
  const { token } = useAuthStore();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversations>({});
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

  const handleSelectDocument = (doc: Document) => {
    setSelectedDocument(doc);
  };

  const handleNewChat = () => {
    if (selectedDocument) {
      setConversations(prev => {
        const newConversations = { ...prev };
        delete newConversations[selectedDocument.id];
        return newConversations;
      });
    }
    setSelectedDocument(null);
  };

  if (!isAuthChecked) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100">
        <p className="animate-pulse text-lg text-blue-700">Đang tải và xác thực...</p>
      </div>
    );
  }

  const currentMessages = selectedDocument ? conversations[selectedDocument.id] || [] : [];

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 antialiased text-gray-800">
      <Sidebar 
        onSelectDocument={handleSelectDocument}
        onNewChat={handleNewChat}
        selectedDocumentId={selectedDocument?.id || null}
      />
      <ChatArea 
        document={selectedDocument} 
        messages={currentMessages}
        setConversations={setConversations}
      />
    </div>
  );
}