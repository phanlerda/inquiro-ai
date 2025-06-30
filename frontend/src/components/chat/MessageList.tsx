'use client';

import { Message } from '@/types/chat';
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
    <div className="flex-grow overflow-y-auto px-2 md:px-6 py-6 space-y-6 custom-scrollbar bg-transparent">
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