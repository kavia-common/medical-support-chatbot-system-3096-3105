import React, { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';
import './index.css';

/**
 * Theme constants aligned to "Ocean Professional"
 */
const THEME = {
  primary: '#2563EB',
  secondary: '#F59E0B',
  error: '#EF4444',
  background: '#f9fafb',
  surface: '#ffffff',
  text: '#111827',
};

/**
 * Utility: Read API base URL from environment
 */
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

/**
 * PUBLIC_INTERFACE
 * buildApiUrl
 * Constructs a URL to the backend REST endpoint.
 * - path: string endpoint path (e.g., "/chat")
 * - params: optional query params object
 */
export function buildApiUrl(path, params) {
  const base = API_BASE_URL.replace(/\/+$/, '');
  const full = `${base}${path.startsWith('/') ? path : `/${path}`}`;
  if (!params) return full;
  const usp = new URLSearchParams(params);
  return `${full}?${usp.toString()}`;
}

/**
 * PUBLIC_INTERFACE
 * ChatMessage component
 * Renders a single chat message (user or agent)
 */
function ChatMessage({ role, content, timestamp }) {
  const isUser = role === 'user';
  return (
    <div
      className="chat-message"
      style={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        background:
          isUser
            ? `linear-gradient(135deg, rgba(37,99,235,0.1), rgba(37,99,235,0.05))`
            : `linear-gradient(135deg, rgba(245,158,11,0.08), rgba(249,250,251,0.6))`,
        border: `1px solid ${isUser ? 'rgba(37,99,235,0.25)' : 'rgba(17,24,39,0.08)'}`,
        color: THEME.text,
      }}
      aria-label={`${isUser ? 'User' : 'Assistant'} message`}
    >
      <div className="chat-message-header">
        <span
          className="chat-role"
          style={{
            color: isUser ? THEME.primary : THEME.secondary,
          }}
        >
          {isUser ? 'You' : 'Medical Assistant'}
        </span>
        {timestamp ? (
          <span className="chat-timestamp" aria-label="timestamp">
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        ) : null}
      </div>
      <div className="chat-content">{content}</div>
    </div>
  );
}

/**
 * PUBLIC_INTERFACE
 * RecommendationCard component
 * Renders a recommendation (e.g., suggested tests/notes) with subtle styling
 */
function RecommendationCard({ title, items = [] }) {
  if (!items.length) return null;
  return (
    <div className="card">
      <div className="card-header">{title}</div>
      <ul className="card-list">
        {items.map((item, idx) => (
          <li key={`${title}-${idx}`} className="card-list-item">
            <span className="dot" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * PUBLIC_INTERFACE
 * HistoryList component
 * Renders a list of previous chat sessions for quick load
 */
function HistoryList({ sessions = [], onSelect }) {
  return (
    <div className="card">
      <div className="card-header">Conversation History</div>
      <div className="history-list">
        {sessions.length === 0 ? (
          <div className="history-empty">No past conversations.</div>
        ) : (
          sessions.map((s) => (
            <button
              key={s.id}
              className="history-item"
              onClick={() => onSelect(s)}
              aria-label={`Load conversation ${s.title || s.id}`}
              title={s.title || s.id}
            >
              <div className="history-title">{s.title || 'Untitled Session'}</div>
              <div className="history-subtitle">
                {new Date(s.updated_at || s.created_at || Date.now()).toLocaleString()}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * PUBLIC_INTERFACE
 * useApi hook
 * Provides typed interaction with REST API endpoints.
 * Assumes the following backend endpoints (adjust paths as needed):
 * - GET /api/chat/history -> [{id, title, created_at, updated_at}]
 * - GET /api/chat/{session_id} -> { id, messages: [{role, content, timestamp}], recommendations: [string] }
 * - POST /api/chat -> { session_id?, message } => returns { id, messages, recommendations }
 */
function useApi() {
  const base = API_BASE_URL;

  const getHistory = async () => {
    const url = buildApiUrl('/api/chat/history');
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch history (${res.status})`);
    return res.json();
  };

  const getSession = async (sessionId) => {
    const url = buildApiUrl(`/api/chat/${encodeURIComponent(sessionId)}`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch session (${res.status})`);
    return res.json();
  };

  const sendMessage = async ({ sessionId, message }) => {
    const url = buildApiUrl('/api/chat');
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId || null, message }),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Failed to send message (${res.status}): ${text}`);
    }
    return res.json();
  };

  return { base, getHistory, getSession, sendMessage };
}

/**
 * PUBLIC_INTERFACE
 * Header component with project title and logo placeholder
 */
function Header() {
  return (
    <header className="header" role="banner" aria-label="Application header">
      <div className="header-left">
        <div className="logo" aria-hidden="true">
          <div className="logo-mark" />
        </div>
        <div className="brand">
          <div className="brand-title">CrewAI Medical Support</div>
          <div className="brand-subtitle">Ocean Professional Interface</div>
        </div>
      </div>
      <div className="header-right">
        <a
          href="https://reactjs.org"
          target="_blank"
          rel="noreferrer"
          className="link"
          aria-label="Learn more about React"
        >
          Docs
        </a>
      </div>
    </header>
  );
}

/**
 * PUBLIC_INTERFACE
 * ChatInput component for sending messages
 */
function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const textRef = useRef(null);

  const send = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
    textRef.current?.focus();
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-input">
      <textarea
        ref={textRef}
        className="chat-textarea"
        rows={1}
        value={value}
        placeholder="Describe your symptoms or ask a question..."
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        disabled={disabled}
        aria-label="Message input"
      />
      <button
        className="btn-primary"
        onClick={send}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        title="Send message"
      >
        Send
      </button>
    </div>
  );
}

/**
 * PUBLIC_INTERFACE
 * Main App component
 * Orchestrates layout, API calls, and state
 */
function App() {
  const { getHistory, getSession, sendMessage } = useApi();

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [recommendations, setRecommendations] = useState([]);

  const scrollRef = useRef(null);

  const disclaimer = useMemo(
    () =>
      'This system does not provide medical advice. It is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.',
    []
  );

  // Load history on mount
  useEffect(() => {
    let ignore = false;
    const load = async () => {
      setHistoryLoading(true);
      setError('');
      try {
        const data = await getHistory();
        if (!ignore) setSessions(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!ignore) setError(e.message || 'Failed to load history');
      } finally {
        if (!ignore) setHistoryLoading(false);
      }
    };
    load();
    return () => {
      ignore = true;
    };
  }, [getHistory]);

  // Auto-scroll chat to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSelectSession = async (s) => {
    setError('');
    setLoading(true);
    try {
      const data = await getSession(s.id);
      setSessionId(data.id || s.id);
      setMessages(Array.isArray(data.messages) ? data.messages : []);
      setRecommendations(Array.isArray(data.recommendations) ? data.recommendations : []);
    } catch (e) {
      setError(e.message || 'Failed to load session');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (text) => {
    setError('');
    setLoading(true);
    const optimisticUser = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, optimisticUser]);
    try {
      const data = await sendMessage({ sessionId, message: text });
      setSessionId(data.id || data.session_id || sessionId);
      setMessages(Array.isArray(data.messages) ? data.messages : []);
      setRecommendations(Array.isArray(data.recommendations) ? data.recommendations : []);
      // refresh history
      getHistory().then((h) => setSessions(Array.isArray(h) ? h : [])).catch(() => {});
    } catch (e) {
      setError(e.message || 'Failed to send message');
      // retain optimistic message on failure, no rollback
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="app-root"
      style={{
        background: THEME.background,
        color: THEME.text,
      }}
    >
      <Header />
      <main className="main">
        <section className="layout">
          {/* Side panel */}
          <aside className="side-panel" aria-label="Side panel with history and recommendations">
            <div className="side-scroll">
              <HistoryList sessions={sessions} onSelect={handleSelectSession} />
              <RecommendationCard title="Recommendations" items={recommendations} />
              <div className="card">
                <div className="card-header" style={{ color: THEME.error }}>
                  Disclaimer
                </div>
                <div className="card-body">
                  <p className="disclaimer">{disclaimer}</p>
                </div>
              </div>
            </div>
          </aside>

          {/* Chat panel */}
          <section className="chat-panel" aria-label="Chat panel">
            <div className="chat-surface">
              <div className="chat-scroll" ref={scrollRef}>
                {!messages.length ? (
                  <div className="empty-state">
                    <div className="empty-badge">Ocean Professional</div>
                    <h2 className="empty-title">Welcome to the Medical Support Assistant</h2>
                    <p className="empty-subtitle">
                      Ask about symptoms, duration, severity, and relevant history. The assistant will summarize,
                      structure notes, and suggest tests or next steps. Always consult a healthcare professional.
                    </p>
                    <div className="prompt-examples">
                      <button className="chip" onClick={() => handleSend('I have a persistent cough and mild fever for 3 days.')}>
                        I have a persistent cough and mild fever for 3 days.
                      </button>
                      <button className="chip" onClick={() => handleSend('Experiencing headaches and nausea after meals.')}>
                        Experiencing headaches and nausea after meals.
                      </button>
                      <button className="chip" onClick={() => handleSend('What tests should I consider for chest pain?')}>
                        What tests should I consider for chest pain?
                      </button>
                    </div>
                  </div>
                ) : (
                  messages.map((m, idx) => (
                    <ChatMessage key={`m-${idx}`} role={m.role} content={m.content} timestamp={m.timestamp} />
                  ))
                )}
              </div>
              <div className="divider" />
              <ChatInput onSend={handleSend} disabled={loading} />
              {error ? (
                <div className="error-banner" role="alert" aria-live="assertive">
                  <span className="error-dot" />
                  <span>{error}</span>
                </div>
              ) : null}
            </div>
          </section>
        </section>
      </main>
      <footer className="footer">
        <span>© {new Date().getFullYear()} CrewAI Medical Support</span>
      </footer>
    </div>
  );
}

export default App;
