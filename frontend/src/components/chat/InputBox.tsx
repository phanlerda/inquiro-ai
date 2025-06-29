// frontend/src/components/chat/InputBox.tsx
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
    <form onSubmit={handleSubmit} className="mt-auto p-4 bg-white border-t">
      <div className="flex items-center">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Nhập câu hỏi của bạn ở đây..."
          disabled={isLoading}
          className="flex-grow px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="ml-3 bg-brand-primary text-white p-3 rounded-full hover:bg-blue-600 disabled:opacity-50 transition-colors duration-150"
        >
          <FiSend size={20} />
        </button>
      </div>
    </form>
  );
}