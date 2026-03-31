import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    if (typeof localStorage === 'undefined') return true;
    const s = localStorage.getItem('autoinsight_theme');
    if (s) return s === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('autoinsight_theme', dark ? 'dark' : 'light');
  }, [dark]);

  const toggle = useCallback(() => setDark((d) => !d), []);

  return (
    <ThemeContext.Provider value={{ dark, setDark, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme needs ThemeProvider');
  return ctx;
}
