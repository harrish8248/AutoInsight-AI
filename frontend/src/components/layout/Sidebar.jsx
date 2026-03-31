import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Lightbulb, FileBarChart, Settings, Sparkles } from 'lucide-react';
import { cn } from '../../lib/cn';

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/insights', icon: Lightbulb, label: 'Insights' },
  { to: '/reports', icon: FileBarChart, label: 'Reports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/10 bg-white/40 backdrop-blur-2xl dark:bg-slate-950/60">
      <div className="flex items-center gap-2 border-b border-white/10 px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 text-white shadow-lg shadow-cyan-500/25">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-slate-900 dark:text-white">AutoInsight</h1>
          <p className="text-xs text-slate-500">AI Analytics</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all',
                isActive
                  ? 'bg-cyan-500/15 text-cyan-700 shadow-inner shadow-cyan-500/10 dark:text-cyan-300'
                  : 'text-slate-600 hover:bg-white/50 dark:text-slate-400 dark:hover:bg-slate-800/50',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-4 text-xs text-slate-500">v1.0 · FastAPI</div>
    </aside>
  );
}
