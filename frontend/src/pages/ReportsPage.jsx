import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import Card from '../components/ui/Card';
import DataTable from '../components/ui/DataTable';

export default function ReportsPage() {
  const { searchQuery } = useOutletContext() || { searchQuery: '' };
  const { sessionId, eda, loading, error } = useAnalysis();

  const rows = useMemo(() => {
    const stats = eda?.summary_statistics || {};
    const list = Object.entries(stats).map(([name, s]) => ({
      id: name,
      column: name,
      mean: s.mean != null ? Number(s.mean).toFixed(4) : '—',
      std: s.std != null ? Number(s.std).toFixed(4) : '—',
      min: s.min != null ? Number(s.min).toFixed(4) : '—',
      max: s.max != null ? Number(s.max).toFixed(4) : '—',
    }));
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter((r) => String(r.column).toLowerCase().includes(q));
  }, [eda, searchQuery]);

  const corrRows = useMemo(() => {
    const c = eda?.correlation;
    if (!c?.columns?.length || !c?.matrix) return [];
    const cols = c.columns;
    const out = [];
    for (let i = 0; i < cols.length; i++) {
      for (let j = i + 1; j < cols.length; j++) {
        const v = c.matrix[i]?.[j];
        if (v != null)
          out.push({
            id: `${cols[i]}-${cols[j]}`,
            a: cols[i],
            b: cols[j],
            r: typeof v === 'number' ? v.toFixed(4) : String(v),
          });
      }
    }
    return out.sort((x, y) => Math.abs(parseFloat(y.r)) - Math.abs(parseFloat(x.r)));
  }, [eda]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Reports</h1>
        <p className="text-slate-500 dark:text-slate-400">Tabular EDA metrics — search and paginate.</p>
      </div>

      {!sessionId && (
        <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-600">
          No dataset loaded. Upload from Dashboard first.
        </p>
      )}

      {sessionId && loading && !eda && (
        <Card>
          <div className="flex h-32 items-center justify-center">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
          </div>
        </Card>
      )}

      {sessionId && error && <Card title="Error"><p className="text-sm text-red-500">{error}</p></Card>}

      {sessionId && eda && !loading && (
        <>
          <Card title="Numeric summary" subtitle="Mean, spread, and range per column">
            <DataTable
              columns={[
                { key: 'column', label: 'Column' },
                { key: 'mean', label: 'Mean' },
                { key: 'std', label: 'Std' },
                { key: 'min', label: 'Min' },
                { key: 'max', label: 'Max' },
              ]}
              rows={rows}
              searchKeys={['column']}
              pageSize={8}
            />
          </Card>

          <Card title="Correlation pairs" subtitle="Sorted by strength">
            <DataTable
              columns={[
                { key: 'a', label: 'Column A' },
                { key: 'b', label: 'Column B' },
                { key: 'r', label: 'r' },
              ]}
              rows={corrRows}
              searchKeys={['a', 'b']}
              pageSize={10}
            />
          </Card>
        </>
      )}
    </motion.div>
  );
}
