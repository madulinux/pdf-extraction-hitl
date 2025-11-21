/**
 * Learning API
 * Model training endpoints - Aligned with backend
 */
import { apiClient } from './client';
import { TrainingMetrics, TrainingHistory, FeedbackStats } from '../types/learning.types';

export const learningAPI = {
  /**
   * Train/retrain CRF model using feedback
   * 
   * Backend: POST /v1/learning/train
   * Returns: { template_id, model_path, training_samples, metrics }
   * 
   * @param templateId - Template ID to train
   * @param useAllFeedback - Use all feedback (true) or only unused (false)
   * @param isIncremental - Incremental training mode (faster, uses only new feedback)
   */
  async train(
    templateId: number, 
    useAllFeedback: boolean = true,
    isIncremental: boolean = false
  ): Promise<{
    template_id: number;
    model_path: string;
    training_samples: number;
    train_metrics: {
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
    };
  }> {
    const response = await apiClient.post<{
      template_id: number;
      model_path: string;
      training_samples: number;
      train_metrics: {
        accuracy: number;
        precision: number;
        recall: number;
        f1: number;
      };
    }>('/v1/learning/train', {
      template_id: templateId,
      use_all_feedback: useAllFeedback,
      is_incremental: isIncremental,
    });

    return response.data.data!;
  },

  /**
   * Get training history for a template
   * 
   * Backend: GET /v1/learning/history/{template_id}
   * Returns: { template_id, history: [...] }
   */
  async getHistory(templateId: number): Promise<{
    template_id: number;
    history: TrainingHistory[];
    count: number;
  }> {
    const response = await apiClient.get<{
      template_id: number;
      history: TrainingHistory[];
    }>(`/v1/learning/history/${templateId}`);
    
    const data = response.data.data!;
    return {
      template_id: data.template_id,
      history: data.history || [],
      count: (response.data.meta?.count as number) || data.history?.length || 0,
    };
  },

  /**
   * Get latest model metrics for a template
   * 
   * Backend: GET /v1/learning/metrics/{template_id}
   * Returns: { template_id, metrics: {...} }
   */
  async getMetrics(templateId: number): Promise<{
    template_id: number;
    metrics: TrainingMetrics;
  }> {
    const response = await apiClient.get<{
      template_id: number;
      metrics: TrainingMetrics;
    }>(`/v1/learning/metrics/${templateId}`);
    
    return response.data.data!;
  },

  /**
   * Get feedback statistics for a template
   * 
   * Backend: GET /v1/learning/feedback-stats/{template_id}
   * Returns: { template_id, stats: {...} }
   */
  async getFeedbackStats(templateId: number): Promise<FeedbackStats> {
    const response = await apiClient.get<FeedbackStats>(`/v1/learning/feedback-stats/${templateId}`);
    
    return response.data.data!;
  },
};

/**
 * Get comprehensive performance metrics for a template
 * Includes accuracy over time, field performance, strategy distribution
 */
export async function getPerformanceMetrics(templateId: number, phase: string = 'baseline'): Promise<import('../types/dashboard.types').PerformanceMetrics> {
  const response = await apiClient.get(`/v1/learning/performance/${templateId}?phase=${phase}`);
  // Backend returns: { success, message, data: {...}, timestamp }
  return response.data.data as import('../types/dashboard.types').PerformanceMetrics;
}

/**
 * Active Learning: Check if document needs validation
 */
export async function checkValidationNeeded(
  extractionResult: Record<string, unknown>,
  threshold: number = 0.7
): Promise<import('../types/dashboard.types').ValidationCheckResult> {
  const response = await apiClient.post('/v1/learning/validate-check', {
    extraction_result: extractionResult,
    threshold,
  });
  // Backend returns: { success, message, data: {...}, timestamp }
  return response.data.data as import('../types/dashboard.types').ValidationCheckResult;
}
