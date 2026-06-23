'use client';

import { useState, useEffect, useRef } from 'react';
import { getMessages, queryAI } from '@/lib/aiApi';
import MessageBubble from '@/components/MessageBubble';
import TypingIndicator from '@/components/TypingIndicator';

interface ChatWindowProps {
  sessionId: string | null;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

const ChatWindow = ({ sessionId }: ChatWindowProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchMessages = async () => {
      if (!sessionId) {
        setMessages([]);
        return;
      }
      try {
        const fetchedMessages = await getMessages(sessionId);
        setMessages(fetchedMessages.map((msg) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
        })));
      } catch (err) {
        setError('Failed to load messages. Please try again.');
      }
    };

    fetchMessages();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const response = await queryAI(query, sessionId);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to send query. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {sessionId ? (
          messages.length > 0 ? (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                sources={message.sources}
              />
            ))
          ) : (
            <p className="text-gray-500 text-center">No messages yet. Start the conversation!</p>
          )
        ) : (
          <p className="text-gray-500 text-center">Select a session to view messages.</p>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 p-4 flex items-center gap-2"
      >
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 resize-none border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
          onKeyDown={(e) => {
            if (e.ctrlKey && e.key === 'Enter') {
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 disabled:bg-gray-300"
          disabled={loading}
        >
          Send
        </button>
      </form>
      {loading && <TypingIndicator />}
      {error && <p className="text-red-500 text-center mt-2">{error}</p>}
    </div>
  );
};

export default ChatWindow;