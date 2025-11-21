/**
 * Learning Types
 */

export interface TrainingMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  training_samples: number;
  trained_at: string;
}

export interface TrainingHistory {
  id: number;
  template_id: number;
  model_path: string;
  training_samples: number;
  accuracy: number;
  precision_score: number;
  recall_score: number;
  f1_score: number;
  trained_at: string;
}

export interface FeedbackStats {
  template_id: number;
  stats: {
    total_feedback: number;
    unused_feedback: number;
    used_feedback: number;
  };
}
