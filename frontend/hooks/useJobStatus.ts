import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

interface Job {
  id: number;
  type: string;
  template_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  last_error?: string;
}

interface UseJobStatusOptions {
  templateId?: number;
  pollInterval?: number; // milliseconds
  enabled?: boolean;
}

/**
 * Hook to monitor job status with polling
 * Uses apiClient for consistent auth and error handling
 */
export function useJobStatus({
  templateId,
  pollInterval = 3000,
  enabled = true,
}: UseJobStatusOptions = {}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    if (!enabled || !templateId) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch active jobs for template using apiClient
      const response = await apiClient.get<{ jobs: Job[]; count: number }>(
        `/v1/jobs?template_id=${templateId}&status=running,pending`
      );

      setJobs(response.data.data?.jobs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [templateId, enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchJobs();

    // Set up polling
    const interval = setInterval(fetchJobs, pollInterval);

    return () => clearInterval(interval);
  }, [fetchJobs, pollInterval, enabled]);

  const hasRunningJob = jobs.some(job => job.status === 'running');
  const hasPendingJob = jobs.some(job => job.status === 'pending');
  const activeJob = jobs.find(job => job.status === 'running' || job.status === 'pending');

  return {
    jobs,
    loading,
    error,
    hasRunningJob,
    hasPendingJob,
    activeJob,
    refetch: fetchJobs,
  };
}
