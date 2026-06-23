// frontend/lib/aiApi.tsx

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("API base URL is not defined in environment variables.");
}

export interface Session {
  id: string;
  name: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface AIQueryResponse {
  answer: string;
  sources: string[];
}

export async function ingestFile(file: File, sessionId: string): Promise<{ chunks_indexed: number }> {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);

  const response = await fetch(`${API_BASE_URL}/api/ai/ingest`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorMessage = await response.text();
    throw new Error(`Failed to ingest file: ${errorMessage}`);
  }

  return response.json();
}

export async function queryAI(query: string, sessionId: string): Promise<AIQueryResponse> {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await fetch(`${API_BASE_URL}/api/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query, session_id: sessionId }),
  });

  if (!response.ok) {
    const errorMessage = await response.text();
    throw new Error(`Failed to query AI: ${errorMessage}`);
  }

  return response.json();
}

export function streamAnswer(query: string, sessionId: string): EventSource {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const url = new URL(`${API_BASE_URL}/api/ai/stream`);
  url.searchParams.append("query", query);
  url.searchParams.append("session_id", sessionId);

  const eventSource = new EventSource(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return eventSource;
}

export async function getSessions(): Promise<Session[]> {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorMessage = await response.text();
    throw new Error(`Failed to fetch sessions: ${errorMessage}`);
  }

  return response.json();
}

export async function createSession(name?: string): Promise<Session> {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const errorMessage = await response.text();
    throw new Error(`Failed to create session: ${errorMessage}`);
  }

  return response.json();
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/messages`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorMessage = await response.text();
    throw new Error(`Failed to fetch messages: ${errorMessage}`);
  }

  return response.json();
}