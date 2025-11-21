/**
 * Dashboard & Performance Metrics Types
 */

export interface FieldPerformance {
  accuracy: number;
  total_extractions: number;
  correct_extractions: number;  // ✅ NEW
  corrections: number;
  avg_confidence: number;
}

// ✅ NEW: Detailed metrics with Precision, Recall, F1-Score
export interface FieldMetricsDetailed {
  precision: number;
  recall: number;
  f1_score: number;
  tp: number;  // True Positives
  fp: number;  // False Positives
  fn: number;  // False Negatives
  support: number;  // Total instances
}

export interface OverviewMetrics {
  total_documents: number;
  validated_documents: number;
  total_corrections: number;
  overall_accuracy: number;
  validation_rate: number;
}

export interface AccuracyDataPoint {
  timestamp: string;
  accuracy: number;
  document_id: number;
  total_fields: number;
  correct_fields: number;
}

export interface FeedbackItem {
  field_name: string;
  original_value: string;
  corrected_value: string;
  timestamp: string;
}

export interface FeedbackStats {
  total_feedback: number;
  feedback_by_field: Record<string, number>;
  recent_feedback: FeedbackItem[];
}

// ✅ NEW: Learning Progress Metrics
export interface BatchProgress {
  batch_number: number;
  start_doc: number;
  end_doc: number;
  accuracy: number;
  total_fields: number;
  correct_fields: number;
}

export interface LearningProgress {
  batches: BatchProgress[];
  improvement_rate: number;
  first_batch_accuracy: number;
  last_batch_accuracy: number;
  total_batches: number;
}

// ✅ NEW: Confidence Trends
export interface StrategyConfidence {
  avg_confidence: number;
  min_confidence: number;
  max_confidence: number;
  sample_count: number;
}

export interface ConfidenceTrend {
  timestamp: string;
  avg_confidence: number;
  document_id: number;
}

export interface ConfidenceTrends {
  overall_trend: ConfidenceTrend[];
  by_strategy: Record<string, StrategyConfidence>;
  avg_confidence: number;
}

// ✅ NEW: Error Patterns
export interface ErrorExample {
  original: string;
  corrected: string;
  timestamp: string;
}

export interface ProblematicField {
  field_name: string;
  error_count: number;
  examples: ErrorExample[];
}

export interface ErrorPatterns {
  most_problematic_fields: ProblematicField[];
  error_frequency: Record<string, number>;
  total_unique_errors: number;
}

// ✅ NEW: Strategy Performance
export interface FieldStrategyPerformance {
  accuracy: number;
  attempts: number;
  correct: number;
}

export interface StrategyPerformance {
  overall_accuracy: number;
  total_attempts: number;
  total_correct: number;
  fields: Record<string, FieldStrategyPerformance>;
}

// ✅ NEW: Performance Stats (Extraction Time)
export interface StrategyTimeStats {
  avg_time_ms: number;
  min_time_ms: number;
  max_time_ms: number;
  count: number;
}

export interface PerformanceStats {
  avg_time_ms: number;
  min_time_ms: number;
  max_time_ms: number;
  total_time_sec: number;
  documents_timed: number;
  by_strategy: Record<string, StrategyTimeStats>;
}

// ✅ NEW: Ablation Study
export interface StrategyComparison {
  strategy: string;
  accuracy: number;
  correct: number;
  total: number;
  coverage: number;
}

export interface AblationStudy {
  strategies: StrategyComparison[];
  hybrid_accuracy: number;
  hybrid_correct: number;
  hybrid_total: number;
  best_single_strategy: string | null;
  best_single_accuracy: number;
  improvement_over_best: number;
}

// ✅ NEW: Time Trends
export interface TimeTrendDataPoint {
  document_id: number;
  timestamp: string;
  extraction_time_ms: number;
  moving_average: number;
  document_number: number;
}

export interface TimeTrends {
  trend_data: TimeTrendDataPoint[];
  avg_time_first_10: number;
  avg_time_last_10: number;
  performance_change: number;
  total_documents: number;
}

// ✅ PHASE 1: Human-in-the-Loop Metrics
export interface HitlMetrics {
  feedback_quality: {
    avg_feedback_per_document: number;
    total_feedback: number;
    documents_with_feedback: number;
    quality_score: number;
  };
  human_effort: {
    total_corrections: number;
    avg_corrections_per_document: number;
    corrections_by_field: Record<string, number>;
  };
  learning_efficiency: {
    feedback_to_improvement_ratio: number;
    total_batches: number;
    avg_improvement_per_batch: number;
  };
}

// ✅ PHASE 1: Adaptive Learning Status
export interface AdaptiveLearningStatus {
  pattern_learning: {
    total_patterns: number;
    active_patterns: number;
    patterns_by_type: Record<string, number>;
    pattern_effectiveness: Record<string, number>;
    avg_pattern_usage: number;
  };
  auto_training: {
    total_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    training_frequency: string;
    last_training: string | null;
    patterns_discovered_total: number;
  };
  recent_jobs: Array<{
    field_name: string;
    status: string;
    patterns_discovered: number;
    patterns_applied: number;
    completed_at: string;
  }>;
}

// ✅ PHASE 1: Incremental Learning
export interface IncrementalBatch {
  batch_number: number;
  batch_size: number;
  document_range: string;
  accuracy_before: number;
  accuracy_after: number;
  improvement: number;
  feedback_count: number;
  learning_efficiency: number;
  documents: number[];
}

export interface IncrementalLearning {
  batches: IncrementalBatch[];
  summary: {
    total_batches: number;
    avg_improvement_per_batch: number;
    total_improvement: number;
    avg_learning_efficiency: number;
    best_batch_number: number | null;
    best_batch_efficiency: number;
    batch_size_used: number;
    optimal_batch_size: number;
  };
}

// ✅ PHASE 1: Baseline Comparison
export interface SystemMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  total_extractions: number;
  correct_extractions: number;
  avg_time_ms: number;
}

export interface BaselineComparison {
  systems: Record<string, SystemMetrics>;
  comparison: {
    best_strategy: string;
    worst_strategy: string;
  };
  improvement: {
    hybrid_over_rule: number;
    hybrid_over_crf: number;
    hybrid_accuracy: number;
  };
}

export interface PerformanceMetrics {
  overview: OverviewMetrics;
  field_performance: Record<string, FieldPerformance>;
  field_metrics_detailed: Record<string, FieldMetricsDetailed>;  // ✅ NEW: Precision, Recall, F1
  strategy_distribution: Record<string, number>;
  strategy_performance: Record<string, StrategyPerformance>;  // ✅ NEW
  accuracy_over_time: AccuracyDataPoint[];
  feedback_stats: FeedbackStats;
  learning_progress: LearningProgress;  // ✅ NEW
  confidence_trends: ConfidenceTrends;  // ✅ NEW
  error_patterns: ErrorPatterns;  // ✅ NEW
  performance_stats: PerformanceStats;  // ✅ NEW: Extraction time
  ablation_study: AblationStudy;  // ✅ NEW: Strategy comparison
  time_trends: TimeTrends;  // ✅ NEW: Time trends
  
  // ✅ PHASE 1: Critical metrics for thesis
  hitl_metrics: HitlMetrics;  // Human-in-the-Loop
  adaptive_learning_status: AdaptiveLearningStatus;  // Pattern learning & auto-training
  incremental_learning: IncrementalLearning;  // Batch-by-batch progress
  baseline_comparison: BaselineComparison;  // vs Traditional approaches
}

export interface ValidationCheckResult {
  should_validate: boolean;
  reason: string;
  threshold: number;
}
