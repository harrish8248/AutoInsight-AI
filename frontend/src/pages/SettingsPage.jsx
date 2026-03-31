import { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import Card from '../components/ui/Card';
import { getApiBaseUrl, setApiBaseUrl } from '../api';
import { useAnalysis } from '../context/AnalysisContext';

export default function SettingsPage() {
  const [url, setUrl] = useState(() => getApiBaseUrl());
  const [err, setErr] = useState('');
  const { autoRefresh, setAutoRefresh, clearSession } = useAnalysis();

  function save(e) {
    e.preventDefault();
    setErr('');
    try {
      const u = new URL(url);
      if (!['http:', 'https:'].includes(u.protocol)) throw new Error('Invalid protocol');
      setApiBaseUrl(u.toString().replace(/\/$/, ''));
      toast.success('API URL saved — refresh if requests fail');
    } catch {
      setErr('Enter a valid http(s) URL (e.g. http://127.0.0.1:8001)');
      toast.error('Invalid URL');
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400">Connection and preferences.</p>
      </div>

      <Card title="Backend API" subtitle="FastAPI base URL (stored in localStorage)">
        <form onSubmit={save} className="space-y-4">
          <div>
            <label htmlFor="api-url" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              API URL
            </label>
            <input
              id="api-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-sm outline-none ring-cyan-500/30 focus:ring-2 dark:border-slate-600 dark:bg-slate-900/80"
              placeholder="http://127.0.0.1:8001"
            />
            {err && <p className="mt-1 text-sm text-red-500">{err}</p>}
          </div>
          <button
            type="submit"
            className="rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/25 transition hover:opacity-95"
          >
            Save
          </button>
        </form>
      </Card>

      <Card title="Theme">
        <p className="text-sm text-slate-500">Use the sun/moon toggle in the top bar for light / dark mode.</p>
      </Card>

      <Card title="Data Refresh">
        <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-sm dark:border-slate-700">
          <span>Enable automatic refresh every 30 seconds</span>
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-cyan-500 focus:ring-cyan-500"
          />
        </label>
      </Card>

      <Card title="Session">
        <button
          type="button"
          onClick={() => {
            clearSession();
            toast.success('Session cleared');
          }}
          className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          Clear loaded dataset
        </button>
      </Card>
    </motion.div>
  );
}
