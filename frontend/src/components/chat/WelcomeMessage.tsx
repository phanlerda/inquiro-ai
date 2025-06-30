'use client';

import { FiHelpCircle, FiFileText, FiInfo } from 'react-icons/fi';

interface WelcomeMessageProps {
  documentName: string;
  onSuggestedQuestionClick: (question: string) => void;
}

const suggestedQuestions = [
  { text: "Tóm tắt nội dung chính của tài liệu này.", icon: <FiInfo /> },
  { text: "Những điểm chính trong tài liệu là gì?", icon: <FiHelpCircle /> },
  { text: "Liệt kê các thuật ngữ quan trọng được đề cập.", icon: <FiFileText /> },
];

export default function WelcomeMessage({ documentName, onSuggestedQuestionClick }: WelcomeMessageProps) {
  return (
    <div className="flex-grow flex flex-col items-center justify-center text-center p-4">
      <h1 className="text-4xl font-extrabold text-blue-700 mb-3 drop-shadow">Bắt đầu Trò chuyện</h1>
      <p className="text-lg text-blue-900 mb-8">
        Bạn đang chat với: <span className="font-semibold">{documentName}</span>
      </p>
      <div className="w-full max-w-2xl">
        <h3 className="text-sm font-semibold text-blue-500 uppercase mb-4 tracking-wider">Hoặc thử một trong các câu hỏi sau:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suggestedQuestions.map((q, index) => (
            <button
              key={index}
              onClick={() => onSuggestedQuestionClick(q.text)}
              className="bg-gradient-to-r from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 text-blue-800 p-4 rounded-xl text-left transition-all duration-150 shadow group border border-blue-100 hover:border-blue-300"
            >
              <div className="flex items-start">
                <span className="text-blue-400 mr-3 mt-1 group-hover:text-blue-600 transition-colors">{q.icon}</span>
                <span>{q.text}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}