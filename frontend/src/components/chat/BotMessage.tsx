'use client';

import ReactMarkdown from 'react-markdown';
import { Source } from '@/types/chat';
import { FiFileText, FiChevronDown, FiChevronUp, FiBox } from 'react-icons/fi';
import { useState } from 'react';

interface BotMessageProps {
  text: string;
  sources?: Source[];
}

export default function BotMessage({ text, sources }: BotMessageProps) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className="flex justify-start mb-4">
      {/* Bot avatar */}
      <div className="flex-shrink-0 mr-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow">
          <FiBox className="text-white w-5 h-5" />
        </div>
      </div>
      <div className="bg-white/90 border border-blue-100 text-gray-800 p-5 rounded-2xl max-w-2xl shadow-md w-full relative">
        <div className="prose prose-sm max-w-none text-gray-900">
          <ReactMarkdown>
            {text}
          </ReactMarkdown>
        </div>
        
        {sources && sources.length > 0 && (
          <div className="mt-4 border-t pt-3">
            <button 
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            >
              {showSources ? <FiChevronUp /> : <FiChevronDown />}
              {showSources ? 'Ẩn nguồn' : `Hiển thị ${sources.length} nguồn trích dẫn`}
            </button>
            {showSources && (
              <div className="mt-3 space-y-2">
                {sources.map((source, index) => (
                  <div key={index} className="bg-blue-50 border border-blue-100 p-3 rounded-xl text-xs shadow-sm">
                    <p className="font-bold text-blue-700 flex items-center mb-1">
                      <FiFileText className="mr-2 shrink-0" />
                      <span className="truncate">Nguồn {index + 1}: {source.filename}</span>
                    </p>
                    <p className="text-gray-700 line-clamp-3">
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