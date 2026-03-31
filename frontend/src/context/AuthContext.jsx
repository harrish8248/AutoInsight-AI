import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api';

const TOKEN_KEY = 'autoinsight_jwt';

const AuthContext = createContext(null);

function readToken() {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY) || null;
}

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [token, setToken] = useState(readToken);

  const isAuthenticated = !!token;

  const persistToken = useCallback((t) => {
    if (typeof localStorage === 'undefined') return;
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  }, []);

  const login = useCallback(
    async ({ email, password }) => {
      const res = await api.post('/auth/login', { email, password });
      const data = res.data || {};
      if (!data.success || !data.access_token) throw new Error(data.detail || data.error || 'Login failed');
      persistToken(data.access_token);
      setToken(data.access_token);
      toast.success('Logged in');
      navigate('/');
      return data;
    },
    [navigate, persistToken],
  );

  const register = useCallback(
    async ({ email, password }) => {
      const res = await api.post('/auth/register', { email, password });
      const data = res.data || {};
      if (!data.success) throw new Error(data.detail || data.error || 'Registration failed');
      toast.success('Account created. Please log in.');
      navigate('/login');
      return data;
    },
    [navigate],
  );

  const logout = useCallback(() => {
    persistToken(null);
    setToken(null);
    toast.success('Logged out');
    navigate('/login');
  }, [navigate, persistToken]);

  const value = useMemo(
    () => ({
      token,
      isAuthenticated,
      login,
      register,
      logout,
    }),
    [token, isAuthenticated, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

