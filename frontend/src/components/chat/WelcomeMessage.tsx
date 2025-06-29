// frontend/src/components/chat/WelcomeMessage.tsx
'use client';

import { FiHelpCircle, FiFileText, FiInfo } from 'react-icons/fi';

// Cập nhật interface props
interface WelcomeMessageProps {
  documentName: string; // Thêm prop này
  onSuggestedQuestionClick: (question: string) => void;
}

// Giả sử có một số câu hỏi gợi ý chung
const suggestedQuestions = [
  { text: "Tóm tắt nội dung chính của tài liệu này.", icon: <FiInfo /> },
  { text: "Những điểm chính trong tài liệu là gì?", icon: <FiHelpCircle /> },
  { text: "Liệt kê các thuật ngữ quan trọng được đề cập.", icon: <FiFileText /> },
];

export default function WelcomeMessage({ documentName, onSuggestedQuestionClick }: WelcomeMessageProps) {
  return (
    <div className="flex-grow flex flex-col items-center justify-center text-center p-4">
      <h1 className="text-4xl font-bold text-gray-800 mb-2">Bắt đầu Trò chuyện</h1>
      {/* Hiển thị tên tài liệu đang được chọn */}
      <p className="text-lg text-gray-500 mb-8">
        Bạn đang chat với: <span className="font-semibold text-gray-700">{documentName}</span>
      </p>
      
      <div className="w-full max-w-2xl">
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Hoặc thử một trong các câu hỏi sau:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suggestedQuestions.map((q, index) => (
            <button
              key={index}
              onClick={() => onSuggestedQuestionClick(q.text)}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 p-4 rounded-lg text-left transition-colors duration-150"
            >
              <div className="flex items-start">
                <span className="text-gray-500 mr-3 mt-1">{q.icon}</span>
                <span>{q.text}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}