import { cn } from '../../lib/cn';

export function Skeleton({ className }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-gradient-to-r from-slate-200 via-slate-100 to-slate-200 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800',
        className,
      )}
    />
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-64 w-full" />
      <div className="flex items-center justify-center gap-3 rounded-xl border border-slate-200/80 bg-white/40 px-4 py-3 text-sm text-slate-600 dark:border-slate-700/80 dark:bg-slate-900/20 dark:text-slate-300">
        <div className="h-3 w-3 animate-pulse rounded-full bg-cyan-500" />
        <span>AI is analyzing your dataset…</span>
      </div>
    </div>
  );
}
