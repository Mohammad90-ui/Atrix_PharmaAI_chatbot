import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  RefreshCw,
  MessageSquare,
  Database,
  FileText,
  Shield,
  Activity,
  Bot,
  User,
  Sparkles,
  Info
} from 'lucide-react';
import './App.css';

const API_URL = "http://localhost:8001";

function App() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);

  // Initialize Session
  useEffect(() => {
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    fetchMetrics();

    // Welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your Clinical Trial Intelligence Assistant. I can help you with drug dosing, adverse events, label cautions, and more. All my answers are grounded in the provided clinical data.",
      source: null
    }]);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_URL}/metrics`);
      setMetrics(res.data);
    } catch (err) {
      console.error("Failed to fetch metrics", err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: inputValue
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        session_id: sessionId,
        user_message: userMsg.content
      });

      const botMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: res.data.assistant_message,
        source: res.data.source_citation,
        isUnknown: res.data.is_unknown,
        isSafety: res.data.is_safety_refusal
      };

      setMessages(prev => [...prev, botMsg]);
      fetchMetrics(); // Update metrics after turn
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: "Only grounded answers are provided. I'm having trouble connecting to the server. Please ensure the backend is running.",
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetChat = async () => {
    try {
      await axios.post(`${API_URL}/reset_session?session_id=${sessionId}`);
      const newSessionId = crypto.randomUUID();
      setSessionId(newSessionId);
      setMessages([{
        id: Date.now(),
        role: 'assistant',
        content: "Conversation reset. How can I help you now?"
      }]);
    } catch (err) {
      console.error("Reset failed", err);
    }
  };

  const examples = [
    "What's the recommended dose for Metformin?",
    "What AEs are reported for Pembrolizumab in melanoma?",
    "Any cautions noted for Nivolumab?",
    "How severe are Imatinib's hematological AEs?"
  ];

  return (
    <div className="app-container">
      {/* Background Ambience */}
      <div className="ambient-bg"></div>

      {/* Main Layout */}
      <div className="main-layout">

        {/* Sidebar */}
        <motion.aside
          className={`sidebar glass ${isSidebarOpen ? 'open' : 'closed'}`}
          initial={{ x: -20 }}
          animate={{ x: 0 }}
        >
          <div className="sidebar-header">
            <div className="logo-area">
              <Sparkles className="icon-pulse" size={24} color="var(--primary)" />
              <h1 className="brand-title">Pharma<span className="text-primary">AI</span></h1>
            </div>
            <p className="subtitle">Clinical Trial Intelligence</p>
          </div>

          <div className="stats-container">
            <h3 className="section-title"><Activity size={16} /> Live Metrics</h3>

            {metrics ? (
              <div className="metrics-grid">
                <MetricCard label="Total Queries" value={metrics.total_turns} color="primary" />
                <div className="metric-row">
                  <span className="label"><Database size={14} /> Excel</span>
                  <span className="val">{metrics.source_usage.excel_only}</span>
                </div>
                <div className="metric-row">
                  <span className="label"><FileText size={14} /> Doc</span>
                  <span className="val">{metrics.source_usage.doc_only}</span>
                </div>
                <div className="metric-row">
                  <span className="label"><Shield size={14} /> Safety</span>
                  <span className="val">{metrics.safety_refusals}</span>
                </div>
              </div>
            ) : (
              <div className="loading-metrics">Loading metrics...</div>
            )}

            <button onClick={fetchMetrics} className="refresh-btn">
              <RefreshCw size={14} /> Refresh Data
            </button>
          </div>
          <br />
          <div className="features-info">
            <h3 className="section-title"><Info size={16} /> Capabilities</h3>
            <ul className="capability-list">
              <li> Grounded Answers</li>
              <li> Source Citations</li>
              <li> Context Memory</li>
              <li> Safety Guardrails</li>
            </ul>
          </div>
        </motion.aside>

        {/* Chat Area */}
        <main className="chat-area">
          <header className="chat-header glass">
            <h2>Clinical Assistant</h2>
            <div className="header-actions">
              <button onClick={resetChat} className="btn btn-secondary btn-sm">
                <RefreshCw size={16} /> New Chat
              </button>
            </div>
          </header>

          <div className="messages-container">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`message-wrapper ${msg.role}`}
                >
                  <div className={`avatar ${msg.role}`}>
                    {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                  </div>

                  <div className="message-content card">
                    <div className="prose">
                      <ReactMarkdown>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {msg.source && msg.source !== 'none' && (
                      <div className="citation-badge">
                        <Database size={12} /> Source: {msg.source}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="message-wrapper assistant"
                >
                  <div className="avatar assistant"><Bot size={20} /></div>
                  <div className="typing-indicator card">
                    <span></span><span></span><span></span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          <footer className="input-area glass">
            {messages.length < 2 && (
              <div className="suggestions">
                {examples.map((ex, i) => (
                  <button key={i} onClick={() => setInputValue(ex)} className="suggestion-chip">
                    {ex}
                  </button>
                ))}
              </div>
            )}

            <form onSubmit={handleSendMessage} className="message-form">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about details from the clinical trials..."
                className="main-input"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="btn btn-primary send-btn"
              >
                <Send size={18} />
              </button>
            </form>
          </footer>
        </main>
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div className={`metric-card ${color}`}>
      <span className="metric-value">{value}</span>
      <span className="metric-label">{label}</span>
    </div>
  );
}

export default App;
