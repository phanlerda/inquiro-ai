'use client';

import { useState, Dispatch, SetStateAction } from 'react';
import { Message, Document } from '@/types/chat';
import MessageList from './MessageList';
import InputBox from './InputBox';
import WelcomeMessage from './WelcomeMessage';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import { Conversations } from '@/app/page';
import { FiLoader } from 'react-icons/fi';

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
    const updatedMessages = [...messages, userMessage];

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
      const historyForAPI: [string, string][] = messages
        .slice(-6)
        .reduce((acc: [string, string][], msg: Message, _, arr: Message[]) => {
          if (msg.sender === 'user' && msg.responseTo) {
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
    <div className="flex-1 p-0 md:p-8 flex flex-col bg-white/80 h-full max-h-screen rounded-tr-3xl rounded-br-3xl shadow-2xl m-0 md:my-8 md:mr-8 transition-all border border-blue-100 backdrop-blur-sm">
      {!document ? (
        <div className="flex-grow flex items-center justify-center text-center p-4">
          <div>
            <h2 className="text-4xl font-extrabold text-blue-700 mb-3 drop-shadow">Chào mừng!</h2>
            <p className="text-gray-500 text-lg">Vui lòng chọn hoặc upload một tài liệu từ sidebar để bắt đầu.</p>
          </div>
        </div>
      ) : messages.length === 0 ? (
        <WelcomeMessage 
          documentName={document.filename} 
          onSuggestedQuestionClick={handleSendMessage} 
        />
      ) : (
        <div className="flex-1 flex flex-col overflow-y-auto custom-scrollbar px-1 md:px-2">
          <MessageList messages={messages} />
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-start p-4 ml-4">
          <div className="bg-gradient-to-r from-blue-100 to-blue-50 border border-blue-200 p-3 rounded-xl flex items-center space-x-2 shadow animate-pulse">
            <FiLoader className="w-5 h-5 text-blue-400 animate-spin" />
            <span className="text-blue-600 text-base font-semibold">Đang trả lời...</span>
          </div>
        </div>
      )}

      {document && (
        <div className="pt-2 pb-4 px-2 md:px-0">
          <InputBox onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      )}
    </div>
  );
}