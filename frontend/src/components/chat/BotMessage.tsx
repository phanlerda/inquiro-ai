// frontend/src/components/chat/BotMessage.tsx
'use client';

import ReactMarkdown from 'react-markdown';
import { Source } from '@/types/chat';
import { FiFileText } from 'react-icons/fi';
import { useState } from 'react';

interface BotMessageProps {
  text: string;
  sources?: Source[];
}

export default function BotMessage({ text, sources }: BotMessageProps) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className="flex justify-start">
      <div className="bg-gray-200 text-gray-800 p-4 rounded-lg max-w-2xl shadow w-full">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>
            {text}
          </ReactMarkdown>
        </div>
        
        {sources && sources.length > 0 && (
          <div className="mt-4 border-t pt-2">
            <button 
              onClick={() => setShowSources(!showSources)}
              className="text-xs font-semibold text-gray-600 hover:text-gray-900"
            >
              {showSources ? 'Ẩn nguồn' : `Hiển thị ${sources.length} nguồn trích dẫn`}
            </button>
            {showSources && (
              <div className="mt-2 space-y-2">
                {sources.map((source, index) => (
                  <div key={index} className="bg-gray-100 p-2 rounded-md text-xs border">
                    <p className="font-bold text-gray-700 flex items-center">
                      <FiFileText className="mr-2 shrink-0" />
                      <span className="truncate">Nguồn {index + 1}: {source.filename}</span>
                    </p>
                    <p className="mt-1 text-gray-600 line-clamp-3">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}