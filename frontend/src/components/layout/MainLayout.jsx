import { useState } from 'react';
import { Navigate, NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Lightbulb, FileBarChart, Settings, MessageCircle } from 'lucide-react';
import { cn } from '../../lib/cn';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { useAnalysis } from '../../context/AnalysisContext';
import { useAuth } from '../../context/AuthContext';

const mobile = [
  { to: '/', icon: LayoutDashboard, label: 'Home' },
  { to: '/insights', icon: Lightbulb, label: 'Insights' },
  { to: '/reports', icon: FileBarChart, label: 'Reports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function MainLayout() {
  const [searchQuery, setSearchQuery] = useState('');
  const { sessionId } = useAnalysis();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-cyan-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="hidden md:block">
        <Sidebar />
      </div>
      <div className="md:pl-64">
        <Navbar searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <main className="p-4 pb-24 md:p-6 md:pb-6">
          <Outlet context={{ searchQuery }} />
        </main>
      </div>
      <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t border-white/10 bg-white/80 backdrop-blur-xl dark:bg-slate-950/90 md:hidden">
        {mobile.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-0.5 text-[10px] font-medium',
                isActive ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-500',
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {sessionId && (
        <NavLink
          to="/insights"
          className="fixed bottom-24 right-5 z-50 hidden items-center gap-2 rounded-full border border-cyan-400/30 bg-gradient-to-r from-cyan-500 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-2xl shadow-cyan-500/30 transition hover:scale-105 md:inline-flex"
        >
          <MessageCircle className="h-4 w-4" />
          AI Assistant
        </NavLink>
      )}
    </div>
  );
}
