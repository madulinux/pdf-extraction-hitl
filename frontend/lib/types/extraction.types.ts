/**
 * Extraction Types
 * Aligned with backend models
 */

export interface FeedbackRecord {
  id: number;
  document_id: number;
  field_name: string;
  original_value: string | null;
  corrected_value: string;
  confidence_score: number | null;
  used_for_training: boolean;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  template_id: number;
  filename: string;
  file_path: string;
  extraction_result: string | ExtractionResult | null; // Can be JSON string or parsed object
  status: 'pending' | 'extracted' | 'validated';
  created_at: string;
  updated_at: string;
  feedback_history?: FeedbackRecord[]; // Feedback history for this document
  template_name?: string;
}

// Conflict detection types
export interface ConflictValue {
  value: string;
  confidence: number;
  page: number;
  label: string | null;
  location_index: number;
  method?: string;
}

export interface FieldConflict {
  detected: boolean;
  level: 'minor' | 'moderate' | 'major';
  similarity: number;
  all_values: ConflictValue[];
  auto_resolved: boolean;
  requires_validation: boolean;
  suggestion?: string;
}

// Backend response structure
export interface ExtractionResult {
  extracted_data: {
    [fieldName: string]: string;
  };
  confidence_scores: {
    [fieldName: string]: number;
  };
  extraction_methods?: {
    [fieldName: string]: string;
  };
  conflicts?: {
    [fieldName: string]: FieldConflict;
  };
  metadata?: {
    pdf_path: string;
    template_id: number;
    template_name: string;
    strategies_used: Array<{
      field: string;
      method: string;
      confidence: number;
      location_index?: number;
      page?: number;
      label?: string;
    }>;
  };
}

export interface Correction {
  field_name: string;
  original_value: string;
  corrected_value: string;
  confidence_score?: number;
}

// Response types for API calls
export interface ExtractResponse {
  document_id: number;
  results: ExtractionResult; // Full extraction result object
  template_id: number;
  filename: string;
}

export interface ValidationResponse {
  feedback_id: number;
  document_id: number;
  corrections_count: number;
}
