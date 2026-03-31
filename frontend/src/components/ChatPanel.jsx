import { useEffect, useRef, useState } from 'react';
import api, { extractApiError, getApiBaseUrl } from '../api';
import Card from './ui/Card';
import { cn } from '../lib/cn';
import ReactMarkdown from 'react-markdown';

function nextId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `m-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ChatPanel({ sessionId, locked }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    setMessages([]);
    setInput('');
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const send = async () => {
    const q = input.trim();
    if (!q || !sessionId || locked || sending) return;
    setSending(true);
    const userId = nextId();
    const assistantId = nextId();
    setMessages((m) => [
      ...m,
      { id: userId, role: 'user', text: q },
      { id: assistantId, role: 'assistant', text: '', confidence: null },
    ]);
    setInput('');
    try {
      const base = getApiBaseUrl().replace(/\/$/, '');
      const token = typeof localStorage !== 'undefined' ? localStorage.getItem('autoinsight_jwt') : null;
      const res = await fetch(`${base}/api/chat_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ session_id: sessionId, question: q }),
      });

      if (!res.ok || !res.body) {
        // Fallback to non-streaming response.
        const { data } = await api.post('/api/chat', { session_id: sessionId, question: q });
        const answer = data.answer ?? '';
        const confidence = data.confidence ?? 'medium';
        setMessages((m) =>
          m.map((msg) =>
            msg.id === assistantId ? { ...msg, text: answer, confidence } : msg,
          ),
        );
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let confidence = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split('\n');
        buffer = parts.pop() || '';

        for (const line of parts) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          let payload;
          try {
            payload = JSON.parse(trimmed);
          } catch {
            continue;
          }
          if (payload.type === 'token') {
            const token = payload.token ?? '';
            setMessages((m) =>
              m.map((msg) => (msg.id === assistantId ? { ...msg, text: (msg.text ?? '') + token } : msg)),
            );
          } else if (payload.type === 'final') {
            confidence = payload.confidence ?? 'medium';
            setMessages((m) =>
              m.map((msg) => (msg.id === assistantId ? { ...msg, confidence: confidence, text: payload.answer ?? msg.text } : msg)),
            );
          }
        }
      }
    } catch (err) {
      const msg = extractApiError(err);
      setMessages((m) =>
        m.map((mmsg) => (mmsg.id === assistantId ? { ...mmsg, text: msg, failed: true } : mmsg)),
      );
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (!sessionId) return null;

  return (
    <Card title="Chat with your data" subtitle="Questions grounded in the current EDA profile">
      <div className="max-h-[420px] space-y-3 overflow-y-auto rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 dark:border-slate-700 dark:bg-slate-900/40">
        {messages.length === 0 && !sending && (
          <p className="text-center text-sm text-slate-500">
            Try: &ldquo;What are the strongest correlations?&rdquo;
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div
              className={cn(
                'max-w-[90%] rounded-2xl px-4 py-2 text-sm',
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-cyan-500 to-violet-600 text-white'
                  : msg.failed
                    ? 'border border-red-300/50 bg-red-950/30 text-red-100'
                    : 'border border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-800',
              )}
            >
              <span className="mb-1 block text-[10px] uppercase tracking-wide opacity-70">
                {msg.role === 'user' ? 'You' : 'AutoInsight'}
              </span>
              <div className="prose prose-sm max-w-none break-words dark:prose-invert">
                <ReactMarkdown>{msg.text || ''}</ReactMarkdown>
              </div>
              {msg.confidence && !msg.failed && (
                <span className="mt-2 inline-block rounded-full border border-slate-200 px-2 py-0.5 text-[10px] dark:border-slate-500">
                  {msg.confidence} confidence
                </span>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm dark:border-slate-600 dark:bg-slate-800">
              <span className="animate-pulse text-slate-500">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
        <textarea
          rows={2}
          placeholder={locked ? 'Waiting for analysis…' : 'Ask a question…'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={locked || sending}
          maxLength={4000}
          className="min-h-[72px] flex-1 resize-y rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm outline-none ring-cyan-500/30 focus:ring-2 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-900/80"
        />
        <button
          type="button"
          onClick={send}
          disabled={locked || sending || !input.trim()}
          className="h-11 shrink-0 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-6 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </Card>
  );
}
