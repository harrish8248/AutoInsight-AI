import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login({ email: email.trim(), password });
    } catch (err) {
      setError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-cyan-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="mx-auto flex min-h-screen max-w-xl items-center p-4">
        <Card
          title="Welcome back"
          subtitle="Log in to your AutoInsight workspace"
          className="w-full bg-white/60 dark:bg-slate-900/40"
          action={null}
        >
          <form className="space-y-4" onSubmit={onSubmit}>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                autoComplete="email"
                required
                className="w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm outline-none ring-cyan-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-950/30"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                autoComplete="current-password"
                required
                className="w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm outline-none ring-cyan-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-950/30"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 disabled:opacity-60"
            >
              {loading ? 'Logging in…' : 'Log in'}
            </button>

            <div className="pt-2 text-center text-sm text-slate-600 dark:text-slate-300">
              No account?{' '}
              <Link to="/register" className="font-semibold text-cyan-600 hover:underline dark:text-cyan-400">
                Create one
              </Link>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}

