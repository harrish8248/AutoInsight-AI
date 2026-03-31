import { motion } from 'framer-motion';
import { cn } from '../../lib/cn';

export default function Card({ children, className, title, subtitle, action }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn(
        'rounded-2xl border border-white/10 bg-white/70 p-5 shadow-lg shadow-slate-900/5 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/60 dark:shadow-black/40',
        className,
      )}
    >
      {(title || subtitle || action) && (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
          <div>
            {title && <h2 className="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </motion.div>
  );
}
