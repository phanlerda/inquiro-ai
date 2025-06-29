// frontend/src/components/chat/MessageList.tsx
'use client';

import { Message } from '@/types/chat'; // Sẽ tạo file types này sau
import UserMessage from './UserMessage';
import BotMessage from './BotMessage';
import { useRef, useEffect } from 'react';

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  return (
    <div className="flex-grow overflow-y-auto p-4 space-y-4">
      {messages.map((msg) =>
        msg.sender === 'user' ? (
          <UserMessage key={msg.id} text={msg.text} />
        ) : (
          <BotMessage key={msg.id} text={msg.text} sources={msg.sources} />
        )
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}