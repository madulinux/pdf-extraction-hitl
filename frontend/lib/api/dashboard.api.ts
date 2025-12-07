/**
 * Dashboard API Client
 * System-wide overview and aggregate metrics
 */

import { apiClient } from "./client";

export interface SystemStats {
  total_documents: number;
  total_validated: number;
  total_feedback: number;
  total_fields: number;
  overall_accuracy: number;
  validation_rate: number;
  active_templates: number;
  total_templates: number;
  // HITL-specific metrics (Tujuan #2 & #3)
  avg_feedback_per_doc: number;
  learning_efficiency: number;
  feedback_utilization_rate: number;
}

export interface TemplateSummary {
  id: number;
  name: string;
  type: string;
  documents: number;
  validated: number;
  accuracy: number;
  feedback_count: number;
  field_count: number;
  status: "active" | "inactive";
  learning_efficiency?: number;  // HITL metric
}

export interface RecentActivity {
  id: number;
  type: "document" | "feedback";
  template_id: number;
  template_name: string;
  filename?: string;
  status?: string;
  timestamp: string;
  validated?: boolean;
  document_id?: number;
  field_name?: string;
}

export interface StrategyDistribution {
  strategy: string;
  count: number;
  avg_accuracy: number;
}

export interface HITLLearningMetrics {
  learning_efficiency: number;
  feedback_utilization_rate: number;
  total_feedback: number;
  feedback_used_for_training: number;
  avg_improvement_per_feedback: number;
}

export interface BatchProgress {
  batch_number: number;
  accuracy: number;
  documents: number;
  feedback_count: number;
}

export interface LearningCurve {
  template_id: number;
  template_name: string;
  template_type: string;
  batches: BatchProgress[];
  final_accuracy: number;
  improvement: number;
}

export interface BaselineAdaptiveMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface BaselineComparison {
  template_id: number;
  template_name: string;
  template_type: string;
  documents: number;
  baseline: BaselineAdaptiveMetrics;
  adaptive: BaselineAdaptiveMetrics;
  improvement: number;
  batches: number;
}

export interface StrategyComparison {
  strategy: string;
  avg_accuracy: number;
  avg_confidence: number;
  usage_count: number;
  high_accuracy_rate: number;
  effectiveness_score: number;
}

export interface SystemOverview {
  system_stats: SystemStats;
  template_summaries: TemplateSummary[];
  hitl_learning_metrics: HITLLearningMetrics;
  strategy_comparison: StrategyComparison[];
  recent_activity: RecentActivity[];
  strategy_distribution: StrategyDistribution[];
  phase: string;
}

export interface TemplateComparison {
  template_id: number;
  template_name: string;
  template_type: string;
  accuracy: number;
  documents: number;
  feedback_count: number;
  avg_confidence: number;
  strategy_preference: string;
}

export interface TrainingJob {
  id: number;
  template_id: number;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export interface ModelStatus {
  template_id: number;
  template_name: string;
  status: string;
  has_model: boolean;
}

export interface SystemHealth {
  status: string;
  database: string;
  training_jobs: {
    total: number;
    running: number;
    completed: number;
    failed: number;
    recent_jobs: TrainingJob[];
  };
  models: ModelStatus[];
  timestamp: string;
}

export const dashboardAPI = {
  /**
   * Get system-wide overview
   */
  getSystemOverview: async (phase?: string): Promise<SystemOverview> => {
    let url = "/v1/dashboard/overview";
    if (phase) {
      url += `?phase=${phase}`;
    }
    const response = await apiClient.get<SystemOverview>(url);
    return response.data.data!;
  },

  /**
   * Get template comparison
   */
  getTemplateComparison: async (
    phase?: string
  ): Promise<{ templates: TemplateComparison[]; phase: string }> => {
    let url = "/v1/dashboard/template-comparison";
    if (phase) {
      url += `?phase=${phase}`;
    }
    const response = await apiClient.get<{
      templates: TemplateComparison[];
      phase: string;
    }>(url);
    return response.data.data!;
  },

  /**
   * Get recent activity
   */
  getRecentActivity: async (
    limit: number = 20,
    phase?: string
  ): Promise<{ activity: RecentActivity[]; count: number; phase: string }> => {
    let url = `/v1/dashboard/recent-activity?limit=${limit}`;
    if (phase) {
      url += `&phase=${phase}`;
    }
    const response = await apiClient.get<{
      activity: RecentActivity[];
      count: number;
      phase: string;
    }>(url);
    return response.data.data!;
  },

  /**
   * Get system health
   */
  getSystemHealth: async (): Promise<SystemHealth> => {
    const response = await apiClient.get<SystemHealth>(
      "/v1/dashboard/system-health"
    );
    return response.data.data!;
  },

  /**
   * Get learning curves for all templates
   */
  getLearningCurves: async (phase: string = "adaptive"): Promise<{
    learning_curves: LearningCurve[];
    phase: string;
  }> => {
    const response = await apiClient.get<{
      learning_curves: LearningCurve[];
      phase: string;
    }>(`/v1/dashboard/learning-curves?phase=${phase}`);
    return response.data.data!;
  },

  /**
   * Get baseline vs adaptive comparison
   */
  getBaselineComparison: async (): Promise<{
    comparison: BaselineComparison[];
    summary: {
      documents: number;
      baseline_accuracy: number;
      adaptive_accuracy: number;
      improvement: number;
      batches: number;
    } | null;
  }> => {
    const response = await apiClient.get<{
      comparison: BaselineComparison[];
      summary: {
        documents: number;
        baseline_accuracy: number;
        adaptive_accuracy: number;
        improvement: number;
        batches: number;
      } | null;
    }>("/v1/dashboard/baseline-comparison");
    return response.data.data!;
  },
};
