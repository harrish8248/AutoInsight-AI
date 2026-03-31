import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api, { extractApiError } from '../api';
import toast from 'react-hot-toast';

const AnalysisContext = createContext(null);

export function AnalysisProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [uploadMeta, setUploadMeta] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [initialToastShown, setInitialToastShown] = useState(false);
  const manualRefreshRef = useRef(false);
  const qc = useQueryClient();

  const onUploaded = useCallback((payload) => {
    setSessionId(payload.sessionId);
    setUploadMeta({
      filename: payload.filename,
      rowCount: payload.rowCount,
      columnCount: payload.columnCount,
      columns: payload.columns,
    });
    toast.success('Dataset uploaded');
    setInitialToastShown(false);
    manualRefreshRef.current = false;
  }, []);

  const clearSession = useCallback(() => {
    if (sessionId) {
      qc.removeQueries({ queryKey: ['analysis', sessionId] });
    }
    setSessionId(null);
    setUploadMeta(null);
    setLastUpdated(null);
  }, [qc, sessionId]);

  const analysisQuery = useQuery({
    queryKey: ['analysis', sessionId],
    enabled: !!sessionId,
    queryFn: async () => {
      const [a, v, i] = await Promise.all([
        api.post('/api/analyze', { session_id: sessionId }),
        api.post('/api/visualize', { session_id: sessionId }),
        api.post('/api/insights', { session_id: sessionId }),
      ]);
      return {
        eda: a.data?.eda ?? null,
        charts: v.data?.charts ?? null,
        insights: i.data?.insights ?? null,
      };
    },
    refetchInterval: sessionId && autoRefresh ? 30000 : false,
    staleTime: 20000,
    retry: 1,
  });

  const loading = sessionId ? analysisQuery.isLoading || analysisQuery.isFetching : false;
  const error = useMemo(
    () => (analysisQuery.isError ? extractApiError(analysisQuery.error) : null),
    [analysisQuery.isError, analysisQuery.error],
  );

  const eda = analysisQuery.data?.eda ?? null;
  const charts = analysisQuery.data?.charts ?? null;
  const insights = analysisQuery.data?.insights ?? null;

  useEffect(() => {
    if (!analysisQuery.isSuccess) return;
    const now = new Date().toISOString();
    setLastUpdated(now);
    const shouldToast = !initialToastShown || manualRefreshRef.current;
    if (shouldToast) {
      toast.success('Analysis ready');
      setInitialToastShown(true);
      manualRefreshRef.current = false;
    }
  }, [analysisQuery.dataUpdatedAt]); // eslint-disable-line react-hooks/exhaustive-deps

  const refreshNow = useCallback(async () => {
    if (!sessionId) return;
    manualRefreshRef.current = true;
    return analysisQuery.refetch();
  }, [analysisQuery, sessionId]);

  const value = {
    sessionId,
    uploadMeta,
    onUploaded,
    clearSession,
    eda,
    charts,
    insights,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    setAutoRefresh,
    refreshNow,
  };

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis needs AnalysisProvider');
  return ctx;
}
