import axios from 'axios';

function defaultBase() {
  if (typeof localStorage !== 'undefined') {
    const s = localStorage.getItem('autoinsight_api_url');
    if (s?.trim()) return s.trim();
  }
  return import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';
}

function getToken() {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem('autoinsight_jwt')?.trim() || null;
}

const api = axios.create({
  baseURL: defaultBase(),
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  config.baseURL = defaultBase();
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  } else if (config.headers?.Authorization) {
    delete config.headers.Authorization;
  }
  return config;
});

if (import.meta.env.DEV) {
  console.log('API URL:', defaultBase());
}

export function setApiBaseUrl(url) {
  const u = url?.trim();
  if (!u) return;
  localStorage.setItem('autoinsight_api_url', u);
  api.defaults.baseURL = u.replace(/\/$/, '');
}

export function getApiBaseUrl() {
  return defaultBase();
}

export function extractApiError(err) {
  const data = err.response?.data;
  if (!data) return err.message || 'Network error';
  const detail = data.detail;
  if (detail && typeof detail === 'object') {
    if (detail.error) {
      return detail.detail ? `${detail.error}: ${detail.detail}` : String(detail.error);
    }
  }
  if (typeof detail === 'string') return detail;
  if (data.error) return String(data.error);
  if (data.message) return String(data.message);
  return err.message || 'Request failed';
}

export default api;
