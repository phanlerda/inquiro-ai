// frontend/src/components/chat/UserMessage.tsx
'use client';

interface UserMessageProps {
  text: string;
}

export default function UserMessage({ text }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <div className="bg-brand-primary text-white p-3 rounded-lg max-w-xl shadow">
        <p>{text}</p>
      </div>
    </div>
  );
}