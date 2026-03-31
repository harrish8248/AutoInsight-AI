import { Line, Bar } from 'react-chartjs-2';
import { useTheme } from '../context/ThemeContext';
import Card from './ui/Card';

function buildOptions(isDark) {
  const tick = isDark ? '#94a3b8' : '#64748b';
  const grid = isDark ? 'rgba(148,163,184,0.12)' : 'rgba(100,116,139,0.12)';
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: tick, font: { size: 12 } } },
      title: { display: false },
    },
    scales: {
      x: { ticks: { color: tick, maxRotation: 45 }, grid: { color: grid } },
      y: { ticks: { color: tick }, grid: { color: grid } },
    },
  };
}

const lineColors = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899'];

function Heatmap({ heatmap, isDark }) {
  if (!heatmap?.values?.length) return null;
  const { x_labels: xLabels, y_labels: yLabels, values, title } = heatmap;
  const flat = values.flat().filter((v) => v != null && !Number.isNaN(v));
  const min = flat.length ? Math.min(...flat, -1) : -1;
  const max = flat.length ? Math.max(...flat, 1) : 1;
  const colorFor = (v) => {
    if (v == null || Number.isNaN(v)) return isDark ? '#1e293b' : '#e2e8f0';
    const t = (v - min) / (max - min || 1);
    const r = Math.round(30 + t * 120);
    const g = Math.round(60 + (1 - Math.abs(t - 0.5) * 2) * 80);
    const b = Math.round(120 + (1 - t) * 100);
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white/40 p-4 dark:border-slate-700 dark:bg-slate-900/40">
      <h3 className="mb-3 text-sm font-semibold text-slate-800 dark:text-slate-100">{title || 'Correlation heatmap'}</h3>
      <div className="max-h-80 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="border border-slate-200 p-1 dark:border-slate-600" />
              {xLabels.map((x) => (
                <th key={x} className="border border-slate-200 bg-slate-50 p-1 dark:border-slate-600 dark:bg-slate-800" title={String(x)}>
                  {String(x).slice(0, 12)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yLabels.map((y, i) => (
              <tr key={y}>
                <th className="border border-slate-200 bg-slate-50 p-1 dark:border-slate-600 dark:bg-slate-800">{String(y).slice(0, 12)}</th>
                {xLabels.map((_, j) => {
                  const v = values[i]?.[j];
                  return (
                    <td
                      key={`${i}-${j}`}
                      className="border border-slate-200 p-1 text-center font-semibold dark:border-slate-600"
                      style={{ background: colorFor(v) }}
                    >
                      {v != null && typeof v === 'number' ? v.toFixed(2) : ''}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Charts({ charts, loading, error }) {
  const { dark } = useTheme();
  const chartOptions = buildOptions(dark);

  if (loading) {
    return (
      <Card title="Visualizations" subtitle="Building charts from your data">
        <div className="flex h-40 items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Visualizations">
        <p className="text-sm text-red-500">{error}</p>
      </Card>
    );
  }

  if (!charts) {
    return (
      <Card title="Visualizations">
        <p className="text-sm text-slate-500">Upload and analyze a dataset to see charts.</p>
      </Card>
    );
  }

  const lines = charts.line ?? [];
  const bars = charts.bar ?? [];
  const heatmap = charts.heatmap;
  const hasAny = lines.length > 0 || bars.length > 0 || heatmap;

  return (
    <Card title="Visualizations" subtitle="Time series, categories, correlations">
      {!hasAny && <p className="text-sm text-slate-500">No chart-ready fields in this dataset.</p>}
      <div className="space-y-6">
        {lines.map((chart, idx) => {
          const data = {
            labels: chart.labels ?? [],
            datasets: (chart.datasets ?? []).map((d, j) => {
              const fallbackColor = lineColors[(idx + j) % lineColors.length];
              const borderColor = d.borderColor ?? fallbackColor;
              const backgroundColor =
                d.backgroundColor ?? (typeof borderColor === "string" ? `${borderColor}33` : `${fallbackColor}33`);
              return {
                label: d.label ?? `Series ${j + 1}`,
                data: d.data ?? [],
                borderColor,
                backgroundColor,
                tension: d.tension ?? 0.25,
                fill: d.fill ?? true,
                showLine: d.showLine ?? true,
                pointRadius: d.pointRadius ?? 3,
                pointHoverRadius: d.pointHoverRadius ?? 5,
              };
            }),
          };
          return (
            <div key={chart.id || idx}>
              <h3 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">{chart.title || 'Line chart'}</h3>
              <div className="chart-box">
                <Line
                  data={data}
                  options={{
                    ...chartOptions,
                    plugins: {
                      ...chartOptions.plugins,
                      legend: {
                        ...chartOptions.plugins.legend,
                        display: (chart.datasets?.length ?? 0) > 1,
                      },
                    },
                  }}
                />
              </div>
            </div>
          );
        })}

        {bars.map((chart, idx) => {
          const data = {
            labels: chart.labels ?? [],
            datasets: (chart.datasets ?? []).map((d) => ({
              label: d.label ?? 'Count',
              data: d.data ?? [],
              backgroundColor: 'rgba(6, 182, 212, 0.55)',
              borderColor: 'rgba(6, 182, 212, 0.95)',
              borderWidth: 1,
            })),
          };
          return (
            <div key={chart.id || `bar-${idx}`}>
              <h3 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">{chart.title || 'Bar chart'}</h3>
              <div className="chart-box">
                <Bar data={data} options={chartOptions} />
              </div>
            </div>
          );
        })}

        {heatmap && <Heatmap heatmap={heatmap} isDark={dark} />}
      </div>
    </Card>
  );
}
