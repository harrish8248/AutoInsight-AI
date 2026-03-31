import { useState } from 'react';
import toast from 'react-hot-toast';
import api, { extractApiError } from '../api';
import Card from './ui/Card';
import { Upload } from 'lucide-react';
import { cn } from '../lib/cn';

export default function UploadZone({ onUploaded, disabled }) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const uploadFile = async (file) => {
    if (!file) return;
    setError(null);
    setLoading(true);
    setProgress(0);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post('/api/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          if (!evt.total) return;
          const p = Math.round((evt.loaded * 100) / evt.total);
          setProgress(p);
        },
      });
      if (!data.success || !data.session_id) throw new Error('Invalid response from server');
      setProgress(100);
      onUploaded({
        sessionId: data.session_id,
        filename: data.filename,
        rowCount: data.row_count,
        columnCount: data.column_count,
        columns: data.columns ?? [],
      });
    } catch (err) {
      const m = extractApiError(err);
      setError(m);
      toast.error(m);
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 400);
    }
  };

  const onInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = '';
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  return (
    <Card
      title="Upload dataset"
      subtitle="CSV or Excel — drag & drop or choose file"
      action={<Upload className="h-5 w-5 text-cyan-500" />}
    >
      {loading && (
        <div className="mb-5 rounded-xl border border-slate-200/70 bg-white/60 p-3 dark:border-slate-700/80 dark:bg-slate-900/30">
          <div className="mb-2 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
            <span>Uploading…</span>
            <span className="font-medium">{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200/60 dark:bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-600 transition-[width] duration-150"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      <div
        className={cn(
          'flex min-h-[120px] flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-4 py-8 transition-all',
          dragOver
            ? 'border-cyan-500 bg-cyan-500/10'
            : 'border-slate-200 bg-slate-50/50 dark:border-slate-600 dark:bg-slate-900/30',
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        role="presentation"
      >
        <input
          type="file"
          accept=".csv,.xlsx,.xls,.xlsm,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
          onChange={onInputChange}
          disabled={disabled || loading}
          className="sr-only"
          id="dataset-file"
        />
        <label
          htmlFor="dataset-file"
          className="cursor-pointer rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/25 transition hover:opacity-95 disabled:opacity-50"
        >
          {loading ? 'Uploading…' : 'Choose file'}
        </label>
        <span className="text-sm text-slate-500">or drop a file here</span>
      </div>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </Card>
  );
}
