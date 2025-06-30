'use client';

import { useState } from 'react';
import { FiSend } from 'react-icons/fi';

interface InputBoxProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function InputBox({ onSendMessage, isLoading }: InputBoxProps) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-auto p-4 bg-white/80 border-t border-blue-100 shadow-inner"
    >
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Nhập câu hỏi của bạn ở đây..."
          disabled={isLoading}
          className="flex-grow px-5 py-3 border border-blue-200 rounded-xl bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-gray-800 placeholder:text-gray-400 text-base shadow-sm"
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="bg-gradient-to-tr from-blue-500 to-blue-700 text-white p-3 rounded-full shadow hover:from-blue-600 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all duration-150 disabled:opacity-50"
          aria-label="Gửi"
        >
          <FiSend size={20} />
        </button>
      </div>
    </form>
  );
}