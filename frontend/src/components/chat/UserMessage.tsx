'use client';

import { FiUser } from 'react-icons/fi';

interface UserMessageProps {
  text: string;
}

export default function UserMessage({ text }: UserMessageProps) {
  return (
    <div className="flex justify-end mb-4">
      <div className="flex items-end gap-2">
        <div className="bg-gradient-to-br from-blue-500 to-blue-700 text-white p-4 rounded-2xl max-w-xl shadow-lg flex items-center">
          <p className="break-words">{text}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shadow">
          <FiUser className="text-white w-4 h-4" />
        </div>
      </div>
    </div>
  );
}