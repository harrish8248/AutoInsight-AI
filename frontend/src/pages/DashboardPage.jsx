import { useOutletContext } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAnalysis } from '../context/AnalysisContext';
import { useTheme } from '../context/ThemeContext';
import UploadZone from '../components/UploadZone';
import Charts from '../components/Charts';
import Card from '../components/ui/Card';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { Activity, Database, Layers, RefreshCw } from 'lucide-react';

export default function DashboardPage() {
  const { searchQuery } = useOutletContext() || { searchQuery: '' };
  const {
    sessionId,
    uploadMeta,
    onUploaded,
    eda,
    charts,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    setAutoRefresh,
    refreshNow,
  } = useAnalysis();
  const { dark } = useTheme();

  const colTypes = eda?.column_types;
  const missing = eda?.missing_values;
  const chartErr = !loading && error ? error : null;

  const cols = uploadMeta?.columns?.filter((c) =>
    searchQuery ? String(c.name).toLowerCase().includes(searchQuery.toLowerCase()) : true,
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400">Upload data, explore metrics, and monitor analysis status.</p>
      </div>

      {sessionId && (
        <Card className="!p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Last updated:{' '}
              <span className="font-medium text-slate-700 dark:text-slate-200">
                {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : '—'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-cyan-500 focus:ring-cyan-400"
                />
                Auto refresh (30s)
              </label>
              <button
                type="button"
                onClick={refreshNow}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-900 dark:hover:bg-slate-800"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh now
              </button>
            </div>
          </div>
        </Card>
      )}

      <UploadZone onUploaded={onUploaded} disabled={false} />

      {!sessionId && (
        <Card>
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-cyan-500/15 p-3 dark:bg-cyan-500/10">
              <Database className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">Get started</h2>
              <p className="mt-1 text-sm text-slate-500">
                Drop a CSV or Excel file. We clean, profile, visualize, and generate AI insights automatically.
              </p>
            </div>
          </div>
        </Card>
      )}

      {sessionId && loading && !eda && <DashboardSkeleton />}

      {sessionId && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: 'Rows', value: uploadMeta?.rowCount ?? '—', icon: Layers },
              { label: 'Columns', value: uploadMeta?.columnCount ?? '—', icon: Database },
              { label: 'Numeric', value: colTypes?.numeric?.length ?? '—', icon: Activity },
              { label: 'Categories', value: colTypes?.categorical?.length ?? '—', icon: Activity },
            ].map(({ label, value, icon: Icon }) => (
              <Card key={label} className="!p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</span>
                  <Icon className="h-4 w-4 text-cyan-500 opacity-80" />
                </div>
                <p className="mt-2 text-2xl font-bold tabular-nums text-slate-900 dark:text-white">{value}</p>
              </Card>
            ))}
          </div>

          <Card
            title="Dataset summary"
            subtitle={uploadMeta?.filename}
            action={
              uploadMeta?.filename && (
                <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">{uploadMeta.filename}</span>
              )
            }
          >
            {error && <p className="text-sm text-red-500">{error}</p>}
            {!loading && !error && uploadMeta && (
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl bg-slate-50/80 p-3 dark:bg-slate-800/50">
                  <p className="text-xs text-slate-500">Datetime columns</p>
                  <p className="text-lg font-semibold">{colTypes?.datetime?.length ?? 0}</p>
                </div>
                <div className="rounded-xl bg-slate-50/80 p-3 dark:bg-slate-800/50">
                  <p className="text-xs text-slate-500">Categorical</p>
                  <p className="text-lg font-semibold">{colTypes?.categorical?.length ?? 0}</p>
                </div>
                <div className="rounded-xl bg-slate-50/80 p-3 dark:bg-slate-800/50">
                  <p className="text-xs text-slate-500">Theme</p>
                  <p className="text-lg font-semibold">{dark ? 'Dark' : 'Light'}</p>
                </div>
              </div>
            )}
            {cols?.length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-medium uppercase text-slate-500">Columns</p>
                <div className="flex flex-wrap gap-2">
                  {cols.map((c) => (
                    <span
                      key={c.name}
                      title={c.dtype}
                      className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-800 dark:text-cyan-200"
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {missing?.by_column && (
              <div className="mt-4 border-t border-slate-200/80 pt-4 dark:border-slate-700">
                <p className="mb-2 text-xs font-medium uppercase text-slate-500">Missing (after cleaning)</p>
                <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
                  {missing.by_column.slice(0, 8).map((row) => (
                    <li key={row.column}>
                      <strong>{row.column}</strong>: {row.missing_count} ({row.missing_pct}%)
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          <Charts charts={charts} loading={loading} error={chartErr} />
        </>
      )}
    </motion.div>
  );
}
