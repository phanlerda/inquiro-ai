// frontend/src/components/chat/ChatArea.tsx
'use client';

import { useState, Dispatch, SetStateAction, useEffect } from 'react';
import { Message, Document } from '@/types/chat';
import MessageList from './MessageList';
import InputBox from './InputBox';
import WelcomeMessage from './WelcomeMessage';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import { Conversations } from '@/app/page';

interface ChatAreaProps {
  document: Document | null;
  messages: Message[];
  setConversations: Dispatch<SetStateAction<Conversations>>;
}

export default function ChatArea({ document, messages, setConversations }: ChatAreaProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuthStore();

  const handleSendMessage = async (query: string) => {
    if (!query.trim() || !document) return;

    const userMessage: Message = { id: uuidv4(), text: query, sender: 'user' };
    
    // Tạo một bản sao của mảng tin nhắn hiện tại và thêm tin nhắn mới của người dùng
    const updatedMessages = [...messages, userMessage];
    
    // Cập nhật state ở component cha
    setConversations(prev => ({
      ...prev,
      [document.id]: updatedMessages,
    }));
    
    setIsLoading(true);

    if (!token) {
        toast.error('Lỗi xác thực. Vui lòng đăng nhập lại.');
        setIsLoading(false);
        return;
    }

    try {
      // --- SỬA LỖI Ở ĐÂY ---
      // Lấy lịch sử từ `messages` (prop), không phải `conversations` (không tồn tại)
      // Thêm kiểu dữ liệu cho các tham số của hàm reduce
      const historyForAPI: [string, string][] = messages
        .slice(-6)
        .reduce((acc: [string, string][], msg: Message, index: number, arr: Message[]) => {
          if (msg.sender === 'user' && msg.responseTo) {
            // Thêm kiểu dữ liệu cho tham số của hàm find
            const botResponse = arr.find((m: Message) => m.id === msg.responseTo);
            if (botResponse && !botResponse.text.startsWith('Lỗi')) {
              acc.push([msg.text, botResponse.text]);
            }
          }
          return acc;
        }, []);

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/`,
        { query, history: historyForAPI, document_id: document.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const botMessage: Message = {
        id: uuidv4(),
        text: response.data.answer,
        sender: 'bot',
        sources: response.data.sources,
        responseTo: userMessage.id,
      };
      
      // Thêm câu trả lời của bot vào state ở component cha
      setConversations(prev => ({
        ...prev,
        [document.id]: [...updatedMessages, botMessage],
      }));

    } catch (error: any) {
      const detailError = error.response?.data?.detail || 'Lỗi khi gọi API. Vui lòng thử lại.';
      toast.error(detailError);
      
      const errorMessage: Message = {
        id: uuidv4(),
        text: detailError,
        sender: 'bot',
        responseTo: userMessage.id,
      };
      
      setConversations(prev => ({
        ...prev,
        [document.id]: [...updatedMessages, errorMessage],
      }));
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="flex-1 p-0 md:p-6 flex flex-col bg-white h-full max-h-screen">
      {!document ? (
        <div className="flex-grow flex items-center justify-center text-center p-4">
          <div>
            <h2 className="text-2xl font-semibold text-gray-700">Chào mừng!</h2>
            <p className="text-gray-500 mt-2">Vui lòng chọn hoặc upload một tài liệu từ sidebar để bắt đầu.</p>
          </div>
        </div>
      ) : messages.length === 0 ? (
        <WelcomeMessage 
            documentName={document.filename} 
            onSuggestedQuestionClick={(q) => handleSendMessage(q)} 
        />
      ) : (
        <MessageList messages={messages} />
      )}
      
      {isLoading && (
        <div className="flex items-center justify-start p-4 ml-4">
          <div className="bg-gray-200 p-3 rounded-lg flex items-center space-x-2 shadow">
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.2s]"></div>
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.4s]"></div>
          </div>
        </div>
      )}
      
      {document && <InputBox onSendMessage={handleSendMessage} isLoading={isLoading} />}
    </div>
  );
}