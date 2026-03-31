import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { cn } from '../../lib/cn';

export default function DataTable({ columns, rows, searchKeys = [], pageSize = 8 }) {
  const [q, setQ] = useState('');
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (!q.trim()) return rows;
    const s = q.toLowerCase();
    const keys = searchKeys.length ? searchKeys : Object.keys(rows[0] || {});
    return rows.filter((r) => keys.some((k) => String(r[k] ?? '').toLowerCase().includes(s)));
  }, [rows, q, searchKeys]);

  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageSafe = Math.min(page, pages - 1);
  const slice = filtered.slice(pageSafe * pageSize, pageSafe * pageSize + pageSize);

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          placeholder="Search rows…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(0);
          }}
          className="w-full rounded-xl border border-slate-200 bg-white/80 py-2 pl-10 pr-4 text-sm outline-none ring-cyan-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-900/80"
        />
      </div>
      <div className="overflow-x-auto rounded-xl border border-slate-200/80 dark:border-slate-700/80">
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/80 dark:border-slate-700 dark:bg-slate-800/50">
              {columns.map((c) => (
                <th key={c.key} className="px-4 py-3 font-medium text-slate-600 dark:text-slate-300">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((row, i) => (
              <tr
                key={row.id ?? i}
                className={cn(
                  'border-b border-slate-100 transition-colors hover:bg-cyan-500/5 dark:border-slate-800',
                )}
              >
                {columns.map((c) => (
                  <td key={c.key} className="px-4 py-2.5 text-slate-700 dark:text-slate-200">
                    {c.render ? c.render(row[c.key], row) : row[c.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>
          {filtered.length} row{filtered.length !== 1 ? 's' : ''}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={pageSafe <= 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="rounded-lg border border-slate-200 p-1.5 disabled:opacity-40 dark:border-slate-600"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span>
            {pageSafe + 1} / {pages}
          </span>
          <button
            type="button"
            disabled={pageSafe >= pages - 1}
            onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            className="rounded-lg border border-slate-200 p-1.5 disabled:opacity-40 dark:border-slate-600"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
