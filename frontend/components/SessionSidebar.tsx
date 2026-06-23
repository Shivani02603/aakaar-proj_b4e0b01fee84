'use client';

import { useEffect, useState } from 'react';
import { getSessions, createSession } from '@/lib/aiApi';
import { formatRelative } from 'date-fns';
import { toast } from 'react-toastify';

interface Session {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

interface SessionSidebarProps {
  onSelectSession: (id: string) => void;
  activeSessionId?: string;
}

export default function SessionSidebar({ onSelectSession, activeSessionId }: SessionSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setLoading(true);
        const fetchedSessions = await getSessions();
        setSessions(fetchedSessions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
      } catch (err) {
        setError('Failed to load sessions. Please try again.');
        toast.error('Failed to load sessions.');
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, []);

  const handleNewChat = async () => {
    try {
      const newSession = await createSession();
      setSessions((prev) => [newSession, ...prev]);
      onSelectSession(newSession.id);
    } catch (err) {
      toast.error('Failed to create a new session.');
    }
  };

  return (
    <div className="w-64 bg-gray-100 border-r border-gray-300 h-full flex flex-col">
      <button
        onClick={handleNewChat}
        className="p-4 text-white bg-blue-500 hover:bg-blue-600 transition-colors text-center font-medium"
      >
        New Chat
      </button>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4">
            {[...Array(3)].map((_, index) => (
              <div key={index} className="h-10 bg-gray-200 rounded mb-2 animate-pulse"></div>
            ))}
          </div>
        ) : error ? (
          <div className="p-4 text-red-500">{error}</div>
        ) : (
          <ul>
            {sessions.map((session) => (
              <li
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`p-4 cursor-pointer ${
                  activeSessionId === session.id
                    ? 'bg-gray-300 border-l-4 border-blue-500'
                    : 'hover:bg-gray-200'
                }`}
              >
                <div className="font-medium truncate">{session.name.slice(0, 30)}</div>
                <div className="text-sm text-gray-500">{formatRelative(new Date(session.created_at), new Date())}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}