import { Session, Message, AIQueryResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error('API base URL is not defined in environment variables.');
}

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authorization token is missing.');
  }
  return { Authorization: `Bearer ${token}` };
};

export const ingestFile = async (file: File, sessionId: string): Promise<{ chunks_indexed: number }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await fetch(`${API_BASE_URL}/api/ai/ingest`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to ingest file.');
  }

  return response.json();
};

export const queryAI = async (query: string, sessionId: string): Promise<AIQueryResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/ai/query`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, session_id: sessionId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to query AI.');
  }

  return response.json();
};

export const streamAnswer = (query: string, sessionId: string): EventSource => {
  const url = `${API_BASE_URL}/api/ai/stream?query=${encodeURIComponent(query)}&session_id=${encodeURIComponent(sessionId)}`;
  const eventSource = new EventSource(url, { headers: getAuthHeaders() });

  return eventSource;
};

export const getSessions = async (): Promise<Session[]> => {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch sessions.');
  }

  return response.json();
};

export const createSession = async (name?: string): Promise<Session> => {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to create session.');
  }

  return response.json();
};

export const getMessages = async (sessionId: string): Promise<Message[]> => {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/messages`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch messages.');
  }

  return response.json();
};