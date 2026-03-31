import Card from './ui/Card';

export default function InsightsPanel({ insights, loading, error }) {
  if (loading && !insights) {
    return (
      <Card title="AI insights">
        <div className="flex h-24 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="AI insights">
        <p className="text-sm text-red-500">{error}</p>
      </Card>
    );
  }

  if (!insights) {
    return (
      <Card title="AI insights">
        <p className="text-sm text-slate-500">Upload a dataset to generate insights.</p>
      </Card>
    );
  }

  const summary = insights.executive_summary ?? '';
  const findings = Array.isArray(insights.key_findings) ? insights.key_findings : [];
  const recommendations = Array.isArray(insights.business_recommendations) ? insights.business_recommendations : [];
  const anomalies = Array.isArray(insights.anomalies) ? insights.anomalies : [];
  const model = insights.model;

  return (
    <Card
      title="AI insights"
      subtitle="Executive summary and recommendations"
      action={
        model ? (
          <span className="rounded-lg bg-cyan-500/15 px-2 py-1 text-xs font-medium text-cyan-700 dark:text-cyan-300">
            {model}
          </span>
        ) : null
      }
    >
      {summary && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-semibold text-cyan-600 dark:text-cyan-400">Executive summary</h3>
          <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-200">{summary}</p>
        </div>
      )}
      {findings.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-semibold text-cyan-600 dark:text-cyan-400">Key findings</h3>
          <ul className="list-inside list-disc space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
            {findings.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      {recommendations.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-cyan-600 dark:text-cyan-400">Recommendations</h3>
          <ul className="list-inside list-disc space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
            {recommendations.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {anomalies.length > 0 && (
        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold text-cyan-600 dark:text-cyan-400">Anomaly detection</h3>
          <ul className="list-inside list-disc space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
            {anomalies.slice(0, 10).map((a, i) => (
              <li key={`${a.column ?? 'col'}-${i}`}>
                <strong className="font-semibold">{a.column}</strong>: {a.outlier_count} outlier(s)
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
