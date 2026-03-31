import { motion } from 'framer-motion';
import { useAnalysis } from '../context/AnalysisContext';
import InsightsPanel from '../components/InsightsPanel';
import ChatPanel from '../components/ChatPanel';

export default function InsightsPage() {
  const { sessionId, insights, loading, error } = useAnalysis();
  const chartErr = !loading && error ? error : null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Insights</h1>
        <p className="text-slate-500 dark:text-slate-400">AI-generated narrative and conversational Q&amp;A.</p>
      </div>
      {!sessionId && (
        <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-600">
          Upload a dataset from the Dashboard to unlock insights.
        </p>
      )}
      {sessionId && (
        <>
          <InsightsPanel insights={insights} loading={loading} error={chartErr} />
          <ChatPanel sessionId={sessionId} locked={loading} />
        </>
      )}
    </motion.div>
  );
}
