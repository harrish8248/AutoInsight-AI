import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './context/ThemeContext';
import { AnalysisProvider } from './context/AnalysisContext';
import { AuthProvider } from './context/AuthContext';
import MainLayout from './components/layout/MainLayout';
import DashboardPage from './pages/DashboardPage';
import InsightsPage from './pages/InsightsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 20_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AnalysisProvider>
          <BrowserRouter>
            <Toaster
              position="top-right"
              toastOptions={{
                className: '!bg-white/95 !text-slate-900 dark:!bg-slate-900/95 dark:!text-slate-100',
                style: { backdropFilter: 'blur(8px)' },
              }}
            />
            <AuthProvider>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route element={<MainLayout />}>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/insights" element={<InsightsPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </AuthProvider>
          </BrowserRouter>
        </AnalysisProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
