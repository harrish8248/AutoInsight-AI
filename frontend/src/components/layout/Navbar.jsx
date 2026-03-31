import { useState } from 'react';
import { Bell, Moon, Search, Sun, User } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar({ searchQuery, onSearchChange }) {
  const { dark, toggle } = useTheme();
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-white/10 bg-white/50 px-6 backdrop-blur-xl dark:bg-slate-950/50">
      <div className="relative max-w-md flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          placeholder="Search columns, metrics…"
          value={searchQuery}
          onChange={(e) => onSearchChange?.(e.target.value)}
          className="w-full rounded-xl border border-slate-200/80 bg-white/80 py-2 pl-10 pr-4 text-sm outline-none ring-cyan-500/20 focus:ring-2 dark:border-slate-700 dark:bg-slate-900/60"
        />
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggle}
          className="rounded-xl border border-slate-200/80 p-2 transition hover:bg-white/80 dark:border-slate-700 dark:hover:bg-slate-800"
          aria-label="Toggle theme"
        >
          {dark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5 text-slate-600" />}
        </button>
        <div className="relative">
          <button
            type="button"
            onClick={() => setNotifOpen((o) => !o)}
            className="rounded-xl border border-slate-200/80 p-2 transition hover:bg-white/80 dark:border-slate-700 dark:hover:bg-slate-800"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5 text-slate-600 dark:text-slate-300" />
          </button>
          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="absolute right-0 mt-2 w-72 rounded-xl border border-white/10 bg-white/95 p-3 text-sm shadow-xl backdrop-blur dark:bg-slate-900/95"
              >
                <p className="font-medium text-slate-900 dark:text-white">Notifications</p>
                <p className="mt-2 text-slate-500">Analysis jobs complete in real time.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-white/80 px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900/60">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 text-xs font-bold text-white">
            <User className="h-4 w-4" />
          </div>
          <span className="hidden text-sm font-medium text-slate-700 sm:inline dark:text-slate-200">You</span>
        </div>
      </div>
    </header>
  );
}
