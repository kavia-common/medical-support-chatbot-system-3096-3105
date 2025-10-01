import React, { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';
import './index.css';
import { API_BASE_URL as API_BASE, apiUrl, apiHealthCheck, fetchExpert } from './api';

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
 * PUBLIC_INTERFACE
 * buildApiUrl
 * Constructs a URL to the backend REST endpoint.
 * - path: string endpoint path (e.g., "/chat")
 * - params: optional query params object
 */
export function buildApiUrl(path, params) {
  const full = apiUrl(path);
  if (!params) return full;
  const usp = new URLSearchParams(params);
  return `${full}?${usp.toString()}`;
}

/**
 * PUBLIC_INTERFACE
 * Structured display helpers for parsing recommendations
 * We detect lines that look like:
 *  - "Test: <name> — Use-case: ... Safety: ...", or
 *  - "Medicine: <name> — Use-case: ... Dosing/Safety: ..." / "Dosing: ... Safety: ..."
 *  - "Support:" / "Option:" items are treated as supportive care
 */
function parseStructuredItems(items = []) {
  const tests = [];
  const medicines = [];
  const support = [];
  const notes = [];
  const disclaimerLines = [];

  const isDisclaimer = (s) =>
    (s || '').toLowerCase().includes('not medical advice') ||
    (s || '').toLowerCase().includes('informational purposes only');

  const normalize = (s) => (s || '').trim();

  for (const raw of items) {
    const line = normalize(raw);
    if (!line) continue;

    if (isDisclaimer(line)) {
      disclaimerLines.push(line);
      continue;
    }

    // Headings emitted by backend flattening
    if (/^Suggested tests\/assessments:/i.test(line)) {
      // skip heading; items will follow
      continue;
    }
    if (/^Suggested medicines\/support:/i.test(line)) {
      // skip heading; items will follow
      continue;
    }
    if (/^Contextual guidance/i.test(line) || /^Selection rationale/i.test(line)) {
      // treat as a contextual note heading and keep
      notes.push(line);
      continue;
    }

    // Detect "Test: ..." pattern
    if (/^Test:/i.test(line) || /^Check:/i.test(line)) {
      tests.push(line);
      continue;
    }

    // Detect medicine/support patterns
    if (/^Medicine:/i.test(line)) {
      medicines.push(line);
      continue;
    }
    if (/^Support:/i.test(line) || /^Option:/i.test(line)) {
      support.push(line);
      continue;
    }

    // Default to notes/context
    notes.push(line);
  }

  // Ensure only unique lines while preserving order
  const dedupe = (arr) => {
    const seen = new Set();
    const out = [];
    for (const s of arr) {
      const k = (s || '').toLowerCase();
      if (!k || seen.has(k)) continue;
      seen.add(k);
      out.push(s);
    }
    return out;
  };

  return {
    tests: dedupe(tests),
    medicines: dedupe(medicines),
    support: dedupe(support),
    notes: dedupe(notes),
    disclaimers: dedupe(disclaimerLines),
  };
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
  const base = API_BASE;

  const ensureConfigured = () => {
    if (!base) {
      throw new Error(
        'API base URL is not configured. Please create medical_chatbot_frontend/.env and set REACT_APP_API_BASE_URL (e.g., http://localhost:8000).'
      );
    }
  };

  const getHistory = async () => {
    ensureConfigured();
    const url = buildApiUrl('/api/chat/history');
    let res;
    try {
      res = await fetch(url);
    } catch (e) {
      throw new Error(`Network error while fetching history. Verify backend is running at ${base}.`);
    }
    if (!res.ok) throw new Error(`Failed to fetch history (${res.status})`);
    return res.json();
  };

  const getSession = async (sessionId) => {
    ensureConfigured();
    const url = buildApiUrl(`/api/chat/${encodeURIComponent(sessionId)}`);
    let res;
    try {
      res = await fetch(url);
    } catch (e) {
      throw new Error(`Network error while fetching session. Verify backend is running at ${base}.`);
    }
    if (!res.ok) throw new Error(`Failed to fetch session (${res.status})`);
    return res.json();
  };

  const sendMessage = async ({ sessionId, message }) => {
    ensureConfigured();
    const url = buildApiUrl('/api/chat');
    let res;
    try {
      res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId || null, message }),
      });
    } catch (e) {
      throw new Error(`Network error while sending message. Verify backend is running at ${base}.`);
    }
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
  const [expertAvailable, setExpertAvailable] = useState(false);
  const [expertTried, setExpertTried] = useState(false);

  // Derived structured suggestions parsed from recommendations
  const structured = useMemo(() => parseStructuredItems(recommendations), [recommendations]);

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
        // quick health check first for clearer diagnostics
        const health = await apiHealthCheck();
        if (!health.ok) {
          throw new Error(
            `Backend health check failed for ${health.url}. ` +
              (health.message || `Status ${health.status}.`) +
              ' Ensure REACT_APP_API_BASE_URL is set to the backend URL.'
          );
        }
        const data = await getHistory();
        if (!ignore) setSessions(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!ignore)
          setError(
            (e && e.message) ||
              'Failed to load history. Verify REACT_APP_API_BASE_URL and backend availability.'
          );
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
    setExpertAvailable(false);
    setExpertTried(false);
    try {
      const data = await getSession(s.id);
      const sid = data.id || s.id;
      setSessionId(sid);
      setMessages(Array.isArray(data.messages) ? data.messages : []);
      // Always attempt to fetch expert and merge with standard
      let merged = Array.isArray(data.recommendations) ? [...data.recommendations] : [];
      const expert = await fetchExpert(sid);
      setExpertTried(true);
      if (expert.ok && Array.isArray(expert.data) && expert.data.length) {
        setExpertAvailable(true);
        // Merge by concatenation; parseStructuredItems will dedupe headings/content
        merged = [...merged, ...expert.data];
      }
      setRecommendations(merged);
    } catch (e) {
      setError(e.message || 'Failed to load session');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (text) => {
    setError('');
    setLoading(true);
    setExpertAvailable(false);
    setExpertTried(false);
    const optimisticUser = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, optimisticUser]);
    try {
      const data = await sendMessage({ sessionId, message: text });
      const sid = data.id || data.session_id || sessionId;
      setSessionId(sid);
      setMessages(Array.isArray(data.messages) ? data.messages : []);
      // Merge inline recommendations with expert endpoint results
      let merged = Array.isArray(data.recommendations) ? [...data.recommendations] : [];
      const expert = await fetchExpert(sid);
      setExpertTried(true);
      if (expert.ok && Array.isArray(expert.data) && expert.data.length) {
        setExpertAvailable(true);
        merged = [...merged, ...expert.data];
      }
      setRecommendations(merged);
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
              {/* Expert enhancement indicator */}
              {expertTried ? (
                <div className="card" aria-live="polite">
                  <div className="card-header">
                    {expertAvailable ? 'Expert suggestions enabled' : 'Expert suggestions unavailable'}
                  </div>
                  <div className="card-body" style={{ color: expertAvailable ? THEME.text : THEME.error }}>
                    {expertAvailable
                      ? 'Enhanced tests and medicine suggestions are shown below.'
                      : 'Expert endpoint returned no data. If you recently updated the backend, please restart the FastAPI server and reload this page.'}
                  </div>
                </div>
              ) : null}
              {/* Structured recommendation sections */}
              <RecommendationCard title="Suggested Tests / Checks" items={structured.tests} />
              <RecommendationCard title="Suggested Medicines" items={structured.medicines} />
              <RecommendationCard title="Supportive Care Options" items={structured.support} />
              <RecommendationCard title="Context & Notes" items={structured.notes} />
              {/* Strong disclaimers, if any parsed */}
              <RecommendationCard title="Important Disclaimer" items={structured.disclaimers.length ? structured.disclaimers : [disclaimer]} />
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
